# ASG DNS Agent

## Purpose

Configuration in this directory creates a minimal set of resources used to demonstrate the ability of the module to create Route53 records for autoscaling groups.  This example is also used in the Terratest unit tests.

## Requirements

- [Terraform](https://www.terraform.io/downloads.html) 0.12+
- [Terraform AWS provider](https://github.com/terraform-providers/terraform-provider-aws) 2.0+

## Usage

To run this example :

```
$ terraform init
$ terraform plan
$ terraform apply
```
