"""Load the Lambda with real SDK clients that can only receive stubbed calls."""

import importlib.util
import socket
import sys
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace

import boto3
import pytest
from botocore.stub import Stubber


@pytest.fixture
def aws(monkeypatch):
    def deny_network(*args, **kwargs):
        pytest.fail("Unit tests must not open network connections")

    monkeypatch.setattr(socket.socket, "connect", deny_network)
    monkeypatch.setattr(socket.socket, "connect_ex", deny_network)
    monkeypatch.setenv("AWS_CONFIG_FILE", "/dev/null")
    monkeypatch.setenv("AWS_SHARED_CREDENTIALS_FILE", "/dev/null")
    monkeypatch.setenv("AWS_EC2_METADATA_DISABLED", "true")
    monkeypatch.delenv("AWS_PROFILE", raising=False)
    monkeypatch.delenv("AWS_DEFAULT_PROFILE", raising=False)
    monkeypatch.delenv("USE_PUBLIC_IP", raising=False)
    monkeypatch.setenv("ROUTE53_TTL", "300")

    session = boto3.Session(
        aws_access_key_id="testing",
        aws_secret_access_key="testing",
        aws_session_token="testing",
        region_name="us-east-1",
    )
    clients = {
        service: session.client(service)
        for service in ("autoscaling", "ec2", "route53")
    }
    monkeypatch.setattr(boto3, "client", clients.__getitem__)
    stubs = {service: Stubber(client) for service, client in clients.items()}

    with ExitStack() as stack:
        for stub in stubs.values():
            stack.enter_context(stub)
        path = Path(__file__).parents[1] / "lambda" / "autoscale" / "autoscale.py"
        spec = importlib.util.spec_from_file_location("autoscale", path)
        module = importlib.util.module_from_spec(spec)
        monkeypatch.setitem(sys.modules, "autoscale", module)
        spec.loader.exec_module(module)
        yield SimpleNamespace(module=module, **stubs)
        for stub in stubs.values():
            stub.assert_no_pending_responses()
