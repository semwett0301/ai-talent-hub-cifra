terraform {
  required_version = ">= 1.6.0"

  # State in DigitalOcean Spaces (S3-compatible). The Spaces region is fixed here,
  # independent of the droplet region — create the bucket in ams3.
  backend "s3" {
    bucket = "cifra-tfstate"
    key    = "cifra/terraform.tfstate"
    region = "us-east-1" # placeholder required by the backend; Spaces ignores it

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
