terraform {
  required_version = ">= 1.6.0"

  # State in DigitalOcean Spaces (S3-compatible). The Spaces region is fixed here,
  # independent of the droplet region — create the bucket in ams3.
  backend "s3" {
    bucket = "cifra-tfstate"
    key    = "cifra/terraform.tfstate"
    # The bucket lives in ams3 (see endpoints). `region` is the AWS SDK signing region
    # and must be a real AWS name — DO docs prescribe us-east-1 for every Spaces region.
    region = "us-east-1"

    endpoints = {
      s3 = "https://ams3.digitaloceanspaces.com"
    }

    skip_credentials_validation = true
    skip_region_validation      = true
    skip_metadata_api_check     = true
    skip_requesting_account_id  = true
    skip_s3_checksum            = true
  }

  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.40"
    }
  }
}

# Auth via the DIGITALOCEAN_TOKEN env var (root .env / GitHub Secret).
provider "digitalocean" {}
