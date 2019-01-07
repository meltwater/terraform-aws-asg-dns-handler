## 0.1.1
- BUG FIXES
  - Solve bug where terraform always changes the filename attribute of the lambda function

## 0.1.0
- BREAKING CHANGES/NOTES
  - Solved race condition described in [FOU-262](https://jira.meltwater.com/browse/FOU-262)
    - Removed `aws_autoscaling_notification` from inside the module, now it's the module that sets up the ASG that should implement this resource, relying on the SNS topic provisioned by this module
    - Added output `autoscale_handling_sns_topic_arn`
    - Removed input `autoscale_group_names`
    - Renamed input `autoscale_update_name` => `autoscale_handler_unique_identifier`

## 0.0.2
- IMPROVEMENTS
  - Take advantage of terraform's `archive_file` data source to dynamically create a zip package for the lambda function

## 0.0.1-original
Initial version of the module, based on: https://github.com/meltwater/terraform-dns/tree/0.0.1/autoscale

Compared to the above:

- BREAKING CHANGES/NOTES
  - none, this is a direct copy
