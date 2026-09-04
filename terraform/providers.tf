terraform {
  required_version = ">= 1.5.0"

  # State in OCI Object Storage (S3-compatible). region + endpoints.s3 are
  # tenancy/region-specific, so they're passed at `init` via -backend-config
  # (see .github/workflows/deploy.yml and terraform/backend.hcl.example).
  backend "s3" {
    bucket = "cifra-tfstate"
    key    = "cifra/oci.tfstate"

    use_path_style              = true
    skip_credentials_validation = true
    skip_region_validation      = true
    skip_metadata_api_check     = true
    skip_requesting_account_id  = true
    skip_s3_checksum            = true
  }

  required_providers {
    oci = {
      source  = "oracle/oci"
      version = "~> 6.0"
    }
  }
}

provider "oci" {
  tenancy_ocid = var.OCI_TENANCY_OCID
  user_ocid    = var.OCI_USER_OCID
  fingerprint  = var.OCI_FINGERPRINT
  private_key  = var.OCI_PRIVATE_KEY
  region       = var.OCI_REGION
}
