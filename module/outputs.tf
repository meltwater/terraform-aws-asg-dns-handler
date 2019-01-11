output "autoscale_handling_sns_topic_arn" {
  value = "${aws_sns_topic.autoscale_handling.arn}"
}
output "autoscale_iam_role_arn" {
  value = "${aws_iam_role.autoscale_handling.arn}"
}

output "agent_lifecycle_iam_role_arn" {
  value = "${aws_iam_role.lifecycle.arn}"
}

