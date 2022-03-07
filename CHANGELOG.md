# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Added

- [#46](https://github.com/meltwater/terraform-aws-asg-dns-handler/pull/46) Create CHANGELOG.md

## [v2.1.4](https://github.com/meltwater/terraform-aws-asg-dns-handler/compare/v2.1.3...v2.1.4) - 2022-03-04

- Update examples and tests [#44](https://github.com/meltwater/terraform-aws-asg-dns-handler/pull/44)

## [v2.1.3](https://github.com/meltwater/terraform-aws-asg-dns-handler/compare/v2.1.2...v2.1.3) - 2021-10-14

### Added

- Added CONTRIBUTING.md file and templates for created issues and pull request.

### Changed

- Improved user docs

## [v2.1.2](https://github.com/meltwater/terraform-aws-asg-dns-handler/compare/v2.1.1...v2.1.2) - 2021-07-16

### Changed

- Changes to readme content to clarify things a bit further.

## [v1.0.5](https://github.com/meltwater/terraform-aws-asg-dns-handler/compare/v1.0.4...v1.0.5) - 2021-07-01

### Changed

- Upgrade Lambda function to use Python 3.8 runtime

## [v2.1.1](https://github.com/meltwater/terraform-aws-asg-dns-handler/compare/v2.1.0...v2.1.1) - 2021-06-28

### Changed

- [#32](https://github.com/meltwater/terraform-aws-asg-dns-handler/pull/32) - Upgrade Lambda runtime to Python3.8.

  This upgrade is being made as AWS is [ending support in Lambda](https://aws.amazon.com/de/blogs/compute/announcing-end-of-support-for-python-2-7-in-aws-lambda/) for the Python 2.7 runtime.

## [v2.1.0](https://github.com/meltwater/terraform-aws-asg-dns-handler/compare/v2.0.1...v2.1.0) - 2020-12-02

### Added

- [#26](https://github.com/meltwater/terraform-aws-asg-dns-handler/pull/26) - Add possibility to use public IP

## [v2.0.1](https://github.com/meltwater/terraform-aws-asg-dns-handler/compare/v2.0.0...v2.0.1) - 2020-11-06

### Changed

- registry.terraform.io to pull in latest changes in master

## [v2.0.0](https://github.com/meltwater/terraform-aws-asg-dns-handler/compare/v1.0.4...v2.0.0) - 2021-07-01

### Changed

- Updating to Terraform 0.12 ([#21](https://github.com/meltwater/terraform-aws-asg-dns-handler/pull/21) [@jimsheldon](https://github.com/jimsheldon))

## [v1.0.4](https://github.com/meltwater/terraform-aws-asg-dns-handler/compare/v1.0.3...v1.0.4 - 2019-11-14

### Added

- Added unique id's to allow multiple uses within the same account ([#17](https://github.com/meltwater/terraform-aws-asg-dns-handler/pull/17) [@seanturner83](https://github.com/seanturner83))

### Changed

- Updated testing scenarios for latest aws provider ([#20](https://github.com/meltwater/terraform-aws-asg-dns-handler/pull/20) [@hikerspath](https://github.com/hikerspath))

## [v1.0.3](https://github.com/meltwater/terraform-aws-asg-dns-handler/compare/v1.0.2...v1.0.3) - 2019-02-11

### Fixed

- Fix for Lifecycle_hooks

## [v1.0.2](https://github.com/meltwater/terraform-aws-asg-dns-handler/compare/v1.0.1...v1.0.2) - 2019-01-21

### Changed

- Outputs.tf and variables.tf updated.

## [v1.0.1](https://github.com/meltwater/terraform-aws-asg-dns-handler/compare/v1.0.2...v1.0.1) - 2019-01-21

### Added

- Initial public release.

