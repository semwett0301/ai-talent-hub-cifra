# ---- OCI access (from the API signing key; see plans/oci-console-setup.md) ----
variable "OCI_TENANCY_OCID" {
  description = "Tenancy OCID."
  type        = string
}

variable "OCI_USER_OCID" {
  description = "User OCID that owns the API signing key."
  type        = string
}

variable "OCI_FINGERPRINT" {
  description = "Fingerprint of the uploaded API signing key."
  type        = string
}

variable "OCI_PRIVATE_KEY" {
  description = "PEM contents of the API signing private key."
  type        = string
  sensitive   = true
}

variable "OCI_REGION" {
  description = "OCI region id, e.g. eu-frankfurt-1."
  type        = string
}

variable "OCI_COMPARTMENT_OCID" {
  description = "Compartment OCID where resources are created (tenancy OCID for root)."
  type        = string
}

# ---- Deploy / app ----
variable "SSH_PUBLIC_KEY" {
  description = "Public SSH key (OpenSSH format) added to the instance."
  type        = string
  sensitive   = true
}

variable "DEPLOY_USER" {
  description = "Non-root user created on the server for SSH/deploy."
  type        = string
  default     = "deploy"
}

variable "SERVER_NAME" {
  description = "Display name of the instance."
  type        = string
  default     = "myapp-prod"
}

variable "APP_NAME" {
  description = "Project name. Used for /opt/<app_name>, hostname and the compose project name."
  type        = string
  default     = "myapp"
}

# ---- Shape (Always Free defaults: ARM A1.Flex 4 OCPU / 24 GB) ----
variable "SHAPE" {
  description = "Instance shape. A1.Flex (ARM) is Always Free; E2.1.Micro (x86) is the fallback."
  type        = string
  default     = "VM.Standard.A1.Flex"
}

variable "OCPUS" {
  description = "OCPUs for a flexible shape (ignored by fixed shapes like E2.1.Micro)."
  type        = number
  default     = 4
}

variable "MEMORY_GB" {
  description = "Memory (GB) for a flexible shape."
  type        = number
  default     = 24
}

variable "BOOT_VOLUME_GB" {
  description = "Boot volume size in GB (Always Free total block storage is 200 GB)."
  type        = number
  default     = 50
}

variable "OS" {
  description = "Image operating system for the oci_core_images lookup."
  type        = string
  default     = "Canonical Ubuntu"
}

variable "OS_VERSION" {
  description = "Image OS version for the lookup."
  type        = string
  default     = "24.04"
}
