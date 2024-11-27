provider "aws" {
  region = var.aws_region
}

terraform {
  backend "s3" {
    bucket         = "flexrp-terraform-state"
    key            = "env/prod/terraform.tfstate"
    region         = "us-west-2"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}

module "networking" {
  source = "../../modules/networking"
  
  environment        = var.environment
  vpc_cidr          = var.vpc_cidr
  private_subnets   = var.private_subnets
  public_subnets    = var.public_subnets
  availability_zones = var.availability_zones
}

# ... more module calls 