module "autoscale_dns" {
  source                              = "../../"
  autoscale_handler_unique_identifier = "asg-handler"
  autoscale_route53zone_arn           = aws_route53_zone.test.id
  vpc_name                            = "asg-handler-vpc"
}

resource "aws_launch_configuration" "test" {
  name_prefix = "asg-handler"

  lifecycle {
    create_before_destroy = true
  }

  image_id                    = var.ami_id
  instance_type               = var.instance_type
  security_groups             = [aws_security_group.test.id]
  associate_public_ip_address = false
}

resource "aws_autoscaling_group" "test" {
  lifecycle {
    create_before_destroy = true
  }

  initial_lifecycle_hook {
    name                    = "${aws_launch_configuration.test.id}-lifecycle-launching"
    default_result          = "ABANDON"
    heartbeat_timeout       = 60
    lifecycle_transition    = "autoscaling:EC2_INSTANCE_LAUNCHING"
    notification_target_arn = module.autoscale_dns.autoscale_handling_sns_topic_arn
    role_arn                = module.autoscale_dns.agent_lifecycle_iam_role_arn
  }

  initial_lifecycle_hook {
    name                    = "${aws_launch_configuration.test.id}-lifecycle-terminating"
    default_result          = "ABANDON"
    heartbeat_timeout       = 60
    lifecycle_transition    = "autoscaling:EC2_INSTANCE_TERMINATING"
    notification_target_arn = module.autoscale_dns.autoscale_handling_sns_topic_arn
    role_arn                = module.autoscale_dns.agent_lifecycle_iam_role_arn
  }

  name = aws_launch_configuration.test.id

  vpc_zone_identifier = module.vpc.private_subnets

  min_size                  = var.min_size
  max_size                  = var.max_size
  health_check_type         = "EC2"
  health_check_grace_period = 300
  force_delete              = false
  launch_configuration      = aws_launch_configuration.test.name
  termination_policies      = ["OldestInstance"]

  tag {
    key                 = "Name"
    value               = "asg-handler"
    propagate_at_launch = true
  }

  tag {
    key                 = "asg:hostname_pattern"
    # Ensure that the value you choose here contains a fully qualified domain name for the zone before the @ symbol
    value               = "asg-test-#instanceid@${aws_route53_zone.test.id}"
    propagate_at_launch = true
  }
}

resource "aws_route53_zone" "test" {
  name          = "asg-handler-vpc.testing"
  force_destroy = true

  vpc {
    vpc_id = module.vpc.vpc_id
  }
}