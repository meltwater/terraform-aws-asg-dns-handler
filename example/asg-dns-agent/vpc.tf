provider "aws" {
  version = "~> 2.0"
  region  = var.aws_region
}

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 2.0"

  name = "asg-handler-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["eu-west-1a", "eu-west-1b", "eu-west-1c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  enable_nat_gateway = true
  enable_vpn_gateway = true
}

resource "aws_security_group" "test" {
  vpc_id = module.vpc.vpc_id
  name   = "asg-handler-vpc-test-agent"

  tags = {
    Name = "asg-handler"
  }

  # allow traffic within security group
  ingress {
    from_port = 0
    to_port   = 0
    protocol  = "-1"

    cidr_blocks = module.vpc.private_subnets_cidr_blocks
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
