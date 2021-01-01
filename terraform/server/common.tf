terraform {
  required_version = ">= 0.14"
  backend "s3" {
    profile        = "maurin"
    bucket         = "terraform.maurin.io"
    key            = "server/terraform.tfstate"
    region         = "eu-west-1"
    dynamodb_table = "terraform-lock"
  }
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 3.0"
    }
  }
}

provider "aws" {
  profile = "maurin"
  region  = "eu-west-1"
}
