terraform {
  backend "s3" {
    bucket = "terraform-state-meltwater-foundation-demo1"
    key    = "eu-west-1/asg-handler-testing/default.tfstate"
    region = "eu-west-1"
  }
}

module "autoscale_dns" {
  source                              = "../../"
  autoscale_handler_unique_identifier = "asg-handler"
  autoscale_route53zone_arn           = "${aws_route53_zone.test.id}"
  vpc_name                            = "asg-handler-vpc"
}

resource "aws_launch_configuration" "test" {
  name_prefix = "asg-handler"

  lifecycle {
    create_before_destroy = true
  }

  image_id                    = "${var.ami_id}"
  instance_type               = "${var.instance_type}"
  security_groups             = ["${aws_security_group.test.id}"]
  associate_public_ip_address = false
}

resource "aws_autoscaling_group" "test" {
  lifecycle {
    create_before_destroy = true
  }

  initial_lifecycle_hook {
    name                    = "${aws_launch_configuration.test.id}-lifecycle-launching"
    default_result          = "CONTINUE"
    heartbeat_timeout       = 60
    lifecycle_transition    = "autoscaling:EC2_INSTANCE_LAUNCHING"
    notification_target_arn = "${module.autoscale_dns.autoscale_handling_sns_topic_arn}"
    role_arn                = "${module.autoscale_dns.agent_lifecycle_iam_role_arn}"
  }

  initial_lifecycle_hook {
    name                    = "${aws_launch_configuration.test.id}-lifecycle-terminating"
    default_result          = "CONTINUE"
    heartbeat_timeout       = 60
    lifecycle_transition    = "autoscaling:EC2_INSTANCE_TERMINATING"
    notification_target_arn = "${module.autoscale_dns.autoscale_handling_sns_topic_arn}"
    role_arn                = "${module.autoscale_dns.agent_lifecycle_iam_role_arn}"
  }

  name                = "${aws_launch_configuration.test.id}"
  vpc_zone_identifier = ["${module.vpc.private_subnets}"]

  min_size                  = "${var.min_size}"
  max_size                  = "${var.max_size}"
  health_check_type         = "EC2"
  health_check_grace_period = 300
  force_delete              = false
  launch_configuration      = "${aws_launch_configuration.test.name}"
  termination_policies      = ["OldestInstance"]

  tag {
    key                 = "Name"
    value               = "asg-handler"
    propagate_at_launch = true
  }

  tag {
    key                 = "asg:hostname_pattern"
    value               = "asg-test-#instanceid.asg-handler-vpc.testing@${aws_route53_zone.test.id}"
    propagate_at_launch = true
  }
}

resource "aws_security_group" "test" {
  vpc_id = "${module.vpc.vpc_id}"
  name   = "asg-handler-vpc-test-agent"

  tags {
    Name = "asg-handler"
  }

  # allow traffic within security group
  ingress {
    from_port = 0
    to_port   = 0
    protocol  = "-1"

    cidr_blocks = [
      "${module.vpc.private_subnets_cidr_blocks}",
    ]
  }

  egress {
    from_port = 0
    to_port   = 0
    protocol  = "-1"

    cidr_blocks = [
      "0.0.0.0/0",
    ]
  }
}
