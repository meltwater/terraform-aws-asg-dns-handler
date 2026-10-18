"""Offline regression tests for the shared stage/prod DNS handler."""

import json
from datetime import UTC, datetime

import pytest
from botocore.exceptions import ClientError

ZONE = "Z123456789"
HOST = "slot.example.test"
ASG = "test-asg"
OLD = "i-0123456789abcdef0"
NEW = "i-0123456789abcdef1"
PRIVATE_IP = "10.0.0.10"
PUBLIC_IP = "192.0.2.10"
LAUNCH = "autoscaling:EC2_INSTANCE_LAUNCHING"
TERMINATE = "autoscaling:EC2_INSTANCE_TERMINATING"
LAUNCH_ERROR = "autoscaling:EC2_INSTANCE_LAUNCH_ERROR"
TOKEN = "00000000-0000-4000-8000-000000000000"


def a_record(ip=PRIVATE_IP, ttl=60):
    return {
        "Name": HOST + ".",
        "Type": "A",
        "TTL": ttl,
        "ResourceRecords": [{"Value": ip}],
    }


def owner_record(instance_id=OLD, ttl=60):
    return {
        "Name": "_asg-owner." + HOST + ".",
        "Type": "TXT",
        "TTL": ttl,
        "ResourceRecords": [{"Value": f'"{instance_id}"'}],
    }


def queue_read(aws, name, record_type, records):
    aws.route53.add_response(
        "list_resource_record_sets",
        {"ResourceRecordSets": records, "IsTruncated": False, "MaxItems": "1"},
        {
            "HostedZoneId": ZONE,
            "StartRecordName": name,
            "StartRecordType": record_type,
            "MaxItems": "1",
        },
    )


def queue_slot(aws, record, owner):
    queue_read(aws, HOST, "A", [record])
    queue_read(aws, "_asg-owner." + HOST, "TXT", [owner] if owner else [])


def change_params(action, records):
    return {
        "HostedZoneId": ZONE,
        "ChangeBatch": {
            "Changes": [
                {"Action": action, "ResourceRecordSet": record} for record in records
            ]
        },
    }


def queue_change(aws, action, records):
    aws.route53.add_response(
        "change_resource_record_sets",
        {
            "ChangeInfo": {
                "Id": "/change/test",
                "Status": "PENDING",
                "SubmittedAt": datetime(2026, 1, 1, tzinfo=UTC),
            }
        },
        change_params(action, records),
    )


def queue_live_instances(aws, pages):
    for index, instances in enumerate(pages):
        response = {"Reservations": [{"Instances": instances}]}
        if index < len(pages) - 1:
            response["NextToken"] = f"page-{index + 1}"
        params = {
            "Filters": [
                {"Name": "tag:aws:autoscaling:groupName", "Values": [ASG]},
                {"Name": "instance-state-name", "Values": ["pending", "running"]},
            ]
        }
        if index:
            params["NextToken"] = f"page-{index}"
        aws.ec2.add_response("describe_instances", response, params)


def queue_metadata(aws, pattern=HOST):
    aws.autoscaling.add_response(
        "describe_tags",
        {"Tags": [{"Key": "asg:hostname_pattern", "Value": f"{pattern}@{ZONE}"}]},
        {
            "Filters": [
                {"Name": "auto-scaling-group", "Values": [ASG]},
                {"Name": "key", "Values": ["asg:hostname_pattern"]},
            ],
            "MaxRecords": 1,
        },
    )


def message(transition=TERMINATE, instance_id=OLD):
    return {
        "LifecycleTransition": transition,
        "AutoScalingGroupName": ASG,
        "EC2InstanceId": instance_id,
        "LifecycleHookName": "dns-hook",
        "LifecycleActionToken": TOKEN,
    }


def sns_event(*messages):
    return {"Records": [{"Sns": {"Message": json.dumps(item)}} for item in messages]}


@pytest.mark.parametrize("use_public", [None, "false", "true", "TRUE"])
def test_fetch_ip_selects_configured_address(aws, monkeypatch, use_public):
    if use_public is not None:
        monkeypatch.setenv("USE_PUBLIC_IP", use_public)
    aws.ec2.add_response(
        "describe_instances",
        {
            "Reservations": [
                {
                    "Instances": [
                        {"PrivateIpAddress": PRIVATE_IP, "PublicIpAddress": PUBLIC_IP}
                    ]
                }
            ]
        },
        {"InstanceIds": [OLD]},
    )

    assert aws.module.fetch_ip_from_ec2(OLD) == (
        PUBLIC_IP if use_public == "true" else PRIVATE_IP
    )


@pytest.mark.parametrize("use_public", ["false", "true"])
def test_live_ips_paginate_filter_exclude_and_ignore_missing_ips(
    aws, monkeypatch, use_public
):
    monkeypatch.setenv("USE_PUBLIC_IP", use_public)
    queue_live_instances(
        aws,
        [
            [
                {
                    "InstanceId": OLD,
                    "PrivateIpAddress": "10.0.0.1",
                    "PublicIpAddress": "192.0.2.1",
                },
                {"InstanceId": NEW},
            ],
            [
                {
                    "InstanceId": NEW,
                    "PrivateIpAddress": PRIVATE_IP,
                    "PublicIpAddress": PUBLIC_IP,
                },
                {
                    "InstanceId": "i-0123456789abcdef2",
                    "PrivateIpAddress": PRIVATE_IP,
                    "PublicIpAddress": PUBLIC_IP,
                },
            ],
        ],
    )

    assert aws.module.fetch_live_ips(ASG, OLD) == {
        PUBLIC_IP if use_public == "true" else PRIVATE_IP
    }


@pytest.mark.parametrize("name", [HOST, HOST.upper(), HOST + "."])
def test_fetch_record_matches_case_and_trailing_dot(aws, name):
    record = a_record()
    queue_read(aws, name, "A", [record])

    assert aws.module.fetch_record(ZONE, name, "A") == record


@pytest.mark.parametrize(
    "records",
    [
        [],
        [{**a_record(), "Name": "slot2.example.test."}],
        [{**a_record(), "Type": "AAAA"}],
    ],
    ids=["absent", "next-name", "wrong-type"],
)
def test_fetch_record_rejects_absent_or_nonmatching_results(aws, records):
    queue_read(aws, HOST, "A", records)

    assert aws.module.fetch_record(ZONE, HOST, "A") is None


def test_fetch_owner_unquotes_instance_id(aws):
    record = owner_record()
    queue_read(aws, "_asg-owner." + HOST, "TXT", [record])

    assert aws.module.fetch_owner(ZONE, HOST) == (OLD, record)


@pytest.mark.parametrize(
    "records",
    [[], [{"Name": "_asg-owner." + HOST + ".", "Type": "TXT", "TTL": 60}]],
)
def test_fetch_owner_missing_or_empty(aws, records):
    queue_read(aws, "_asg-owner." + HOST, "TXT", records)

    assert aws.module.fetch_owner(ZONE, HOST) == (None, None)


@pytest.mark.parametrize(
    "pattern, expected",
    [(HOST, HOST), ("node-#instanceid.example.test", f"node-{OLD}.example.test")],
)
def test_build_hostname(aws, pattern, expected):
    assert aws.module.build_hostname(pattern, OLD) == expected


def test_launch_upserts_address_and_dedicated_owner_atomically(aws, monkeypatch):
    monkeypatch.setenv("ROUTE53_TTL", "120")
    queue_metadata(aws)
    aws.ec2.add_response(
        "describe_instances",
        {"Reservations": [{"Instances": [{"PrivateIpAddress": PRIVATE_IP}]}]},
        {"InstanceIds": [OLD]},
    )
    aws.ec2.add_response(
        "create_tags",
        {},
        {"Resources": [OLD], "Tags": [{"Key": "Name", "Value": "slot"}]},
    )
    # A single expected API call ensures the A and owner cannot be written separately.
    queue_change(
        aws,
        "UPSERT",
        [
            {**a_record(ttl=120), "Name": HOST},
            {**owner_record(ttl=120), "Name": "_asg-owner." + HOST},
        ],
    )

    aws.module.process_message(message(LAUNCH))


@pytest.mark.parametrize("transition", [TERMINATE, LAUNCH_ERROR])
@pytest.mark.parametrize(
    "replacement_ip", [PRIVATE_IP, "10.0.0.20"], ids=["reused-ip", "new-ip"]
)
def test_stale_termination_cannot_delete_replacement_record(
    aws, transition, replacement_ip
):
    queue_metadata(aws)
    queue_slot(aws, a_record(replacement_ip), owner_record(NEW))

    # No mutation or EC2 call is queued: either would fail immediately.
    aws.module.process_message(message(transition))


def test_owned_delete_preserves_exact_record_sets_and_is_idempotent(aws):
    record = a_record(ttl=42)
    owner = owner_record(ttl=73)
    queue_slot(aws, record, owner)
    queue_change(aws, "DELETE", [record, owner])
    queue_read(aws, HOST, "A", [])

    aws.module.delete_record(ZONE, HOST, ASG, OLD)
    aws.module.delete_record(ZONE, HOST, ASG, OLD)


def test_retried_delete_after_replacement_launch_preserves_new_owner(aws):
    old_address, old_owner = a_record(), owner_record()
    queue_slot(aws, old_address, old_owner)
    queue_change(aws, "DELETE", [old_address, old_owner])
    queue_slot(aws, a_record(), owner_record(NEW))

    aws.module.delete_record(ZONE, HOST, ASG, OLD)
    aws.module.delete_record(ZONE, HOST, ASG, OLD)


@pytest.mark.parametrize(
    "records", [[], [{**a_record(), "Name": "slot2.example.test."}]]
)
def test_delete_missing_record_never_touches_next_record(aws, records):
    queue_read(aws, HOST, "A", records)

    aws.module.delete_record(ZONE, HOST, ASG, OLD)


@pytest.mark.parametrize("use_public", ["false", "true"])
def test_legacy_record_held_by_live_replacement_is_preserved(
    aws, monkeypatch, use_public
):
    monkeypatch.setenv("USE_PUBLIC_IP", use_public)
    ip = PUBLIC_IP if use_public == "true" else PRIVATE_IP
    queue_slot(aws, a_record(ip), None)
    queue_live_instances(
        aws,
        [
            [
                {
                    "InstanceId": NEW,
                    "PrivateIpAddress": PRIVATE_IP,
                    "PublicIpAddress": PUBLIC_IP,
                }
            ]
        ],
    )

    aws.module.delete_record(ZONE, HOST, ASG, OLD)


def test_legacy_stale_record_is_deleted_using_original_ttl(aws):
    record = a_record(ttl=42)
    queue_slot(aws, record, None)
    queue_live_instances(
        aws, [[{"InstanceId": OLD, "PrivateIpAddress": PRIVATE_IP}], []]
    )
    queue_change(aws, "DELETE", [record])

    aws.module.delete_record(ZONE, HOST, ASG, OLD)


def test_route53_rejecting_concurrent_owner_change_propagates_for_retry(aws):
    queue_metadata(aws)
    record, owner = a_record(), owner_record()
    queue_slot(aws, record, owner)
    # If ownership changes after the reads, the exact TXT delete no longer matches.
    aws.route53.add_client_error(
        "change_resource_record_sets",
        service_error_code="InvalidChangeBatch",
        service_message="The record values do not match the current values",
        expected_params=change_params("DELETE", [record, owner]),
    )

    with pytest.raises(ClientError, match="InvalidChangeBatch"):
        aws.module.lambda_handler(sns_event(message()), None)


@pytest.mark.parametrize("service", ["route53", "ec2"])
def test_failed_safety_lookup_does_not_delete_or_complete_lifecycle(aws, service):
    queue_metadata(aws)
    if service == "ec2":
        queue_slot(aws, a_record(), None)
        operation = "describe_instances"
    else:
        operation = "list_resource_record_sets"
    getattr(aws, service).add_client_error(operation, service_error_code="AccessDenied")

    with pytest.raises(ClientError, match="AccessDenied"):
        aws.module.lambda_handler(sns_event(message()), None)


def test_handler_completes_lifecycle_after_safe_skip(aws):
    queue_metadata(aws)
    queue_slot(aws, a_record(), owner_record(NEW))
    aws.autoscaling.add_response(
        "complete_lifecycle_action",
        {},
        {
            "LifecycleHookName": "dns-hook",
            "AutoScalingGroupName": ASG,
            "InstanceId": OLD,
            "LifecycleActionToken": TOKEN,
            "LifecycleActionResult": "CONTINUE",
        },
    )

    aws.module.lambda_handler(sns_event(message()), None)


def test_handler_processes_all_sns_records_without_lifecycle_metadata(aws, caplog):
    queue_metadata(aws)
    queue_read(aws, HOST, "A", [])
    aws.module.lambda_handler(
        sns_event(
            {"Event": "autoscaling:TEST_NOTIFICATION"},
            {
                key: value
                for key, value in message().items()
                if key not in {"LifecycleHookName", "LifecycleActionToken"}
            },
        ),
        None,
    )

    assert "No valid JSON message" in caplog.text


def test_unknown_transition_does_not_mutate_dns(aws, caplog):
    queue_metadata(aws)

    aws.module.process_message(message("autoscaling:UNKNOWN"))

    assert "Encountered unknown event type" in caplog.text


def test_invalid_sns_json_propagates(aws):
    with pytest.raises(json.JSONDecodeError):
        aws.module.lambda_handler({"Records": [{"Sns": {"Message": "invalid"}}]}, None)
