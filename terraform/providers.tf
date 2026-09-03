terraform {
  required_version = ">= 1.5.0"

  backend "s3" {
    bucket = "cifra-tfstate"
    key    = "cifra/terraform.tfstate"
    region = "ru-1"

    endpoints                   = { s3 = "https://s3.twcstorage.ru" }
    use_path_style              = true
    skip_credentials_validation = true
    skip_region_validation      = true
    skip_metadata_api_check     = true
    skip_requesting_account_id  = true
    skip_s3_checksum            = true
  }

  required_providers {
    twc = {
      source  = "timeweb-cloud/timeweb-cloud"
      version = "~> 1.8"
    }
  }
}

provider "twc" {}
