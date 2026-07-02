terraform {
  required_version = ">= 1.6.0, < 2.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # For v0.1, using local state
  # Remote state (S3 + DynamoDB) can be added in future versions
}
