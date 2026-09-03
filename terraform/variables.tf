variable "SSH_PUBLIC_KEY" {
  description = "Public SSH key (OpenSSH format); uploaded to Timeweb by Terraform."
  type        = string
  sensitive   = true
}

variable "DEPLOY_USER" {
  description = "Non-root user created on the server for SSH/deploy."
  type        = string
  default     = "deploy"
}

variable "SERVER_NAME" {
  description = "Display name of the server in the panel."
  type        = string
  default     = "myapp-prod"
}

variable "APP_NAME" {
  description = "Project name. Used for /opt/<app_name>, hostname and the compose project name."
  type        = string
  default     = "myapp"
}

variable "LOCATION" {
  description = "Location: ru-1 (spb), ru-2 (nsk), ru-3 (msk), de-1, kz-1, nl-1."
  type        = string
  default     = "ru-3"
}

variable "AVAILABILITY_ZONE" {
  description = "Availability zone; must match the location (ru-1=spb-3, ru-2=nsk-1, ru-3=msk-1)."
  type        = string
  default     = "msk-1"
}

variable "OS_NAME" {
  description = "OS family name for the data lookup."
  type        = string
  default     = "ubuntu"
}

variable "OS_VERSION" {
  description = "OS version; must exist paired with the Docker software image."
  type        = string
  default     = "24.04"
}

variable "CPU" {
  description = "Number of vCPU."
  type        = number
  default     = 2
}

variable "RAM_MB" {
  description = "RAM in MB; must be a multiple of 1024."
  type        = number
  default     = 4096

  validation {
    condition     = var.RAM_MB % 1024 == 0
    error_message = "RAM must be a multiple of 1024 MB."
  }
}

variable "DISK_MB" {
  description = "System disk size in MB."
  type        = number
  default     = 30720
}

variable "PRESET_TYPE" {
  description = "Configurator preset type: premium, standard, gpu, dedicated_cpu."
  type        = string
  default     = "standard"
}
