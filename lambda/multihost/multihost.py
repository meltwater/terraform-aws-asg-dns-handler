import json
import logging
import boto3
import sys
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

autoscaling = boto3.client('autoscaling')
ec2 = boto3.client('ec2')
route53 = boto3.client('route53')

HOSTNAME_TAG_NAME = "asg:multihost_pattern"

LIFECYCLE_KEY = "LifecycleHookName"
ASG_KEY = "AutoScalingGroupName"

# Constrints of running a pool
# If multiple events are happening in quick succession we may get into situiations where latter runs pickup instances that have not finished terminating.
# In situiations were multiple terminations are expected it may be better to change the logic from
#  * Scanning the ASG and building the IP list from there
# to
#  * Grabbing the IP list from EC2 and stripping out the instance. This may require more information to be stored in TXT entries to map instance ID's to IP addresses
# In general it is expected that on busy ASG's there will be residual IP's

# Fetches IP of an instance via EC2 API
def fetch_ip_from_ec2(instance_id):
    logger.info("Fetching IP for instance-id: %s", instance_id)
    ip_address = None
    ec2_response = ec2.describe_instances(InstanceIds=[instance_id])['Reservations'][0]['Instances'][0]
    if ec2_response['State']['Name'] == 'running':
      if 'use_public_ip' in os.environ and os.environ['use_public_ip'] == "true":
        try:
          ip_address = ec2_response['PublicIpAddress']
          logger.info("Found public IP for instance-id %s: %s", instance_id, ip_address)
        except:
          logger.info("No public IP for instance-id %s: %s", instance_id, ip_address)
      else:
        try:
          ip_address = ec2_response['PrivateIpAddress']
          logger.info("Found private IP for instance-id %s: %s", instance_id, ip_address)
        except:
          logger.info("No private IP for instance-id %s: %s", instance_id, ip_address)

    return ip_address

# Fetches IP of an instance via route53 API
def fetch_ip_from_route53(hostname, zone_id):
    logger.info("Fetching IP for hostname: %s", hostname)

    ip_address = route53.list_resource_record_sets(
        HostedZoneId=zone_id,
        StartRecordName=hostname,
        StartRecordType='A',
        MaxItems='1'
    )['ResourceRecordSets'][0]['ResourceRecords'][0]['Value']

    logger.info("Found IP for hostname %s: %s", hostname, ip_address)

    return ip_address

# Fetches relevant tags from ASG
# Returns tuple of hostname_pattern, zone_id
def fetch_tag_metadata(asg_name):
    logger.info("Fetching tags for ASG: %s", asg_name)

    tag_value = autoscaling.describe_tags(
        Filters=[
            {'Name': 'auto-scaling-group','Values': [asg_name]},
            {'Name': 'key','Values': [HOSTNAME_TAG_NAME]}
        ],
        MaxRecords=1
    )['Tags'][0]['Value']

    logger.info("Found tags for ASG %s: %s", asg_name, tag_value)

    return tag_value.split("@")

# Updates the name tag of an instance
def update_name_tag(instance_id, hostname):
    tag_name = hostname.split('.')[0]
    logger.info("Updating name tag for instance-id %s with: %s", instance_id, tag_name)
    ec2.create_tags(
        Resources = [
            instance_id
        ],
        Tags = [
            {
                'Key': 'Name',
                'Value': tag_name
            }
        ]
    )

# Updates a Route53 record
def update_record(zone_id, ips, hostname):
    if len(ips) == 0:
      ips.append({'Value': fetch_ip_from_route53(hostname, zone_id)})
      operation = 'DELETE'
    else:
      operation = 'UPSERT'
    logger.info("Changing record with %s for %s -> %s in %s", operation, hostname, ips, zone_id)
    route53.change_resource_record_sets(
        HostedZoneId=zone_id,
        ChangeBatch={
            'Changes': [
                {
                    'Action': operation,
                    'ResourceRecordSet': {
                        'Name': hostname,
                        'Type': 'A',
                        'TTL': 300,
                        'ResourceRecords': ips
                    }
                }
            ]
        }
    )

def process_asg(auto_scaling_group_name, hostname, ignore_instance):
  # Iterate through the instance group: Put IP addresses into a list and update the instance names to match the group.
  # ignore_instance should only be provided if we are terminating an instance.
  ips = []
  # IP's is a list of dictionaries [{'Value': ipAddr1},{'Value': ipAddr2}] eg [{'Value':'127.0.0.1'}]
  if ignore_instance is None:
    logger.info("Processing ASG %s", auto_scaling_group_name)
  else:
    logger.info("Ignoring instance-id %s while Processing ASG %s", ignore_instance, auto_scaling_group_name)
  for instance in autoscaling.describe_auto_scaling_groups(AutoScalingGroupNames=[auto_scaling_group_name])['AutoScalingGroups'][0]['Instances']:
    if ignore_instance != instance['InstanceId']:
      ipAddr = fetch_ip_from_ec2(instance['InstanceId'])
      if ipAddr is not None:
        ips.append({'Value': ipAddr})
        update_name_tag(instance['InstanceId'], hostname)
  return ips


  # Processes a scaling event
  # Builds a hostname from tag metadata, fetches a IP, and updates records accordingly
def process_message(message):
    if 'LifecycleTransition' not in message:
        logger.info("Processing %s event", message['Event'])
        return
    logger.info("Processing %s event", message['LifecycleTransition'])

    if message['LifecycleTransition'] not in ("autoscaling:EC2_INSTANCE_LAUNCHING","autoscaling:EC2_INSTANCE_TERMINATING", "autoscaling:EC2_INSTANCE_LAUNCH_ERROR"):
      logger.error("Encountered unknown event type: %s", message['LifecycleTransition'])

    asg_name    = message['AutoScalingGroupName']
    instance_id = message['EC2InstanceId']

    ignore_instance = None
    if message['LifecycleTransition'] == 'autoscaling:EC2_INSTANCE_TERMINATING':
      ignore_instance = instance_id
      logger.info("The following instance-id should be ignored %s", instance_id)

    hostname, zone_id = fetch_tag_metadata(asg_name)

    ip_addrs = process_asg(asg_name, hostname, ignore_instance)
    update_record(zone_id, ip_addrs, hostname)

# Picks out the message from a SNS message and deserializes it
def process_record(record):
    process_message(json.loads(record['Sns']['Message']))

# Main handler where the SNS events end up to
# Events are bulked up, so process each Record individually
def lambda_handler(event, context):
    logger.info("Processing SNS event: " + json.dumps(event))

    for record in event['Records']:
        process_record(record)

# Finish the asg lifecycle operation by sending a continue result
    logger.info("Finishing ASG action")
    message = json.loads(record['Sns']['Message'])
    if LIFECYCLE_KEY in message and ASG_KEY in message :
        response = autoscaling.complete_lifecycle_action (
            LifecycleHookName     = message['LifecycleHookName'],
            AutoScalingGroupName  = message['AutoScalingGroupName'],
            InstanceId            = message['EC2InstanceId'],
            LifecycleActionToken  = message['LifecycleActionToken'],
            LifecycleActionResult = 'CONTINUE'
        )
        logger.info("ASG action complete: %s", response)
    else :
        logger.error("No valid JSON message")

# if invoked manually, assume someone pipes in a event json
if __name__ == "__main__":
    logging.basicConfig()

    lambda_handler(json.load(sys.stdin), None)

