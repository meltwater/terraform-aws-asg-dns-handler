import json
import logging
import os
import sys

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

autoscaling = boto3.client("autoscaling")
ec2 = boto3.client("ec2")
route53 = boto3.client("route53")

HOSTNAME_TAG_NAME = "asg:hostname_pattern"

LIFECYCLE_KEY = "LifecycleHookName"
ASG_KEY = "AutoScalingGroupName"

# Dedicated name for the ownership TXT so it never collides with a real TXT RRset at the hostname
OWNER_RECORD_PREFIX = "_asg-owner."


# Fetches IP of an instance via EC2 API
def fetch_ip_from_ec2(instance_id):
    logger.info("Fetching IP for instance-id: %s", instance_id)
    ec2_response = ec2.describe_instances(InstanceIds=[instance_id])
    if "USE_PUBLIC_IP" in os.environ and os.environ["USE_PUBLIC_IP"] == "true":
        ip_address = ec2_response["Reservations"][0]["Instances"][0]["PublicIpAddress"]
        logger.info("Found public IP for instance-id %s: %s", instance_id, ip_address)
    else:
        ip_address = ec2_response["Reservations"][0]["Instances"][0]["PrivateIpAddress"]
        logger.info("Found private IP for instance-id %s: %s", instance_id, ip_address)

    return ip_address


# Private/public IPs of the ASG's live (pending/running) instances, excluding one id
def fetch_live_ips(asg_name, exclude_instance_id):
    use_public = os.environ.get("USE_PUBLIC_IP") == "true"
    ips = set()
    for page in ec2.get_paginator("describe_instances").paginate(
        Filters=[
            {"Name": "tag:aws:autoscaling:groupName", "Values": [asg_name]},
            {"Name": "instance-state-name", "Values": ["pending", "running"]},
        ]
    ):
        for reservation in page["Reservations"]:
            for instance in reservation["Instances"]:
                if instance["InstanceId"] == exclude_instance_id:
                    continue
                ip = (
                    instance.get("PublicIpAddress")
                    if use_public
                    else instance.get("PrivateIpAddress")
                )
                if ip:
                    ips.add(ip)
    return ips


# Exact Name+Type lookup; returns the ResourceRecordSet or None if absent
def fetch_record(zone_id, hostname, record_type):
    response = route53.list_resource_record_sets(
        HostedZoneId=zone_id,
        StartRecordName=hostname,
        StartRecordType=record_type,
        MaxItems="1",
    )
    record_sets = response["ResourceRecordSets"]
    if not record_sets:
        return None
    record = record_sets[0]
    if (
        record["Name"].rstrip(".").lower() != hostname.rstrip(".").lower()
        or record["Type"] != record_type
    ):
        return None
    return record


# Reads the owner instance-id from the companion TXT record; returns (owner_id, record)
def fetch_owner(zone_id, hostname):
    record = fetch_record(zone_id, OWNER_RECORD_PREFIX + hostname, "TXT")
    if record is None or not record.get("ResourceRecords"):
        return None, None
    return record["ResourceRecords"][0]["Value"].strip('"'), record


# Fetches relevant tags from ASG
# Returns tuple of hostname_pattern, zone_id
def fetch_tag_metadata(asg_name):
    logger.info("Fetching tags for ASG: %s", asg_name)

    tag_value = autoscaling.describe_tags(
        Filters=[
            {"Name": "auto-scaling-group", "Values": [asg_name]},
            {"Name": "key", "Values": [HOSTNAME_TAG_NAME]},
        ],
        MaxRecords=1,
    )["Tags"][0]["Value"]

    logger.info("Found tags for ASG %s: %s", asg_name, tag_value)

    return tag_value.split("@")


# Builds a hostname according to pattern
def build_hostname(hostname_pattern, instance_id):
    return hostname_pattern.replace("#instanceid", instance_id)


# Updates the name tag of an instance
def update_name_tag(instance_id, hostname):
    tag_name = hostname.split(".")[0]
    logger.info("Updating name tag for instance-id %s with: %s", instance_id, tag_name)
    ec2.create_tags(Resources=[instance_id], Tags=[{"Key": "Name", "Value": tag_name}])


# Submits a Route53 change batch (atomic across the given changes)
def change_records(zone_id, changes):
    route53.change_resource_record_sets(
        HostedZoneId=zone_id, ChangeBatch={"Changes": changes}
    )


def record_set(hostname, record_type, ttl, value):
    return {
        "Name": hostname,
        "Type": record_type,
        "TTL": ttl,
        "ResourceRecords": [{"Value": value}],
    }


# Upserts the A record and a companion TXT owner record (= instance_id) atomically
def upsert_record(zone_id, ip, hostname, instance_id, ttl):
    logger.info(
        "Changing record with UPSERT for %s -> %s (owner %s) in %s",
        hostname,
        ip,
        instance_id,
        zone_id,
    )
    change_records(
        zone_id,
        [
            {
                "Action": "UPSERT",
                "ResourceRecordSet": record_set(hostname, "A", ttl, ip),
            },
            {
                "Action": "UPSERT",
                "ResourceRecordSet": record_set(
                    OWNER_RECORD_PREFIX + hostname, "TXT", ttl, '"%s"' % instance_id
                ),
            },
        ],
    )


# Deletes the record only if it still belongs to the terminating instance
def delete_record(zone_id, hostname, asg_name, instance_id):
    a_record = fetch_record(zone_id, hostname, "A")
    if a_record is None:
        logger.info("No A record for %s; nothing to delete", hostname)
        return

    owner, txt_record = fetch_owner(zone_id, hostname)
    if owner is not None:
        if owner != instance_id:
            logger.info(
                "Skipping delete for %s: slot owned by %s, not %s",
                hostname,
                owner,
                instance_id,
            )
            return
        logger.info(
            "Changing record with DELETE for %s (owner %s departing) in %s",
            hostname,
            instance_id,
            zone_id,
        )
        changes = [{"Action": "DELETE", "ResourceRecordSet": a_record}]
        if txt_record is not None:
            changes.append({"Action": "DELETE", "ResourceRecordSet": txt_record})
        change_records(zone_id, changes)
        return

    # No owner tag yet (un-warmed slot): skip if a live instance holds this record
    record_ip = a_record["ResourceRecords"][0]["Value"]
    if record_ip in fetch_live_ips(asg_name, instance_id):
        logger.info(
            "Skipping delete for %s: no owner tag but %s is held by a live instance",
            hostname,
            record_ip,
        )
        return
    logger.info(
        "Changing record with DELETE for %s -> %s (no owner tag, stale) in %s",
        hostname,
        record_ip,
        zone_id,
    )
    change_records(zone_id, [{"Action": "DELETE", "ResourceRecordSet": a_record}])


# Processes a scaling event
# Builds a hostname from tag metadata, fetches a IP, and updates records accordingly
def process_message(message):
    if "LifecycleTransition" not in message:
        logger.info("Processing %s event", message["Event"])
        return
    logger.info("Processing %s event", message["LifecycleTransition"])

    transition = message["LifecycleTransition"]
    asg_name = message["AutoScalingGroupName"]
    instance_id = message["EC2InstanceId"]

    hostname_pattern, zone_id = fetch_tag_metadata(asg_name)
    hostname = build_hostname(hostname_pattern, instance_id)

    if transition == "autoscaling:EC2_INSTANCE_LAUNCHING":
        ip = fetch_ip_from_ec2(instance_id)
        update_name_tag(instance_id, hostname)
        upsert_record(
            zone_id, ip, hostname, instance_id, int(os.environ["ROUTE53_TTL"])
        )
    elif (
        transition == "autoscaling:EC2_INSTANCE_TERMINATING"
        or transition == "autoscaling:EC2_INSTANCE_LAUNCH_ERROR"
    ):
        delete_record(zone_id, hostname, asg_name, instance_id)
    else:
        logger.error("Encountered unknown event type: %s", transition)


# Picks out the message from a SNS message and deserializes it
def process_record(record):
    process_message(json.loads(record["Sns"]["Message"]))


# Main handler where the SNS events end up to
# Events are bulked up, so process each Record individually
def lambda_handler(event, context):
    logger.info("Processing SNS event: " + json.dumps(event))

    for record in event["Records"]:
        process_record(record)

    # Finish the asg lifecycle operation by sending a continue result
    logger.info("Finishing ASG action")
    message = json.loads(record["Sns"]["Message"])
    if LIFECYCLE_KEY in message and ASG_KEY in message:
        response = autoscaling.complete_lifecycle_action(
            LifecycleHookName=message["LifecycleHookName"],
            AutoScalingGroupName=message["AutoScalingGroupName"],
            InstanceId=message["EC2InstanceId"],
            LifecycleActionToken=message["LifecycleActionToken"],
            LifecycleActionResult="CONTINUE",
        )
        logger.info("ASG action complete: %s", response)
    else:
        logger.error("No valid JSON message")


# if invoked manually, assume someone pipes in a event json
if __name__ == "__main__":
    logging.basicConfig()

    lambda_handler(json.load(sys.stdin), None)
