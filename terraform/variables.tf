variable "twc_token" {
  description = "Timeweb Cloud API token. Prefer the TWC_TOKEN environment variable."
  type        = string
  sensitive   = true
  default     = null
}

variable "ssh_key_name" {
  description = "Name of the SSH key as saved in the Timeweb Cloud panel."
  type        = string
}

variable "server_name" {
  description = "Display name of the server in the panel."
  type        = string
  default     = "myapp-prod"
}

variable "app_name" {
  description = "Project name. Used for /opt/<app_name>, hostname and the compose project name."
  type        = string
  default     = "myapp"
}

variable "location" {
  description = "Location: ru-1, ru-2, ru-3, de-1, kz-1, nl-1."
  type        = string
  default     = "ru-1"
}

variable "availability_zone" {
  description = "Availability zone within the location; null picks one automatically."
  type        = string
  default     = null
}

variable "os_name" {
  description = "OS family name for the data lookup."
  type        = string
  default     = "ubuntu"
}

variable "os_version" {
  description = "OS version; must exist paired with the Docker software image."
  type        = string
  default     = "24.04"
}

variable "cpu" {
  description = "Number of vCPU."
  type        = number
  default     = 2
}

variable "ram_mb" {
  description = "RAM in MB; must be a multiple of 1024."
  type        = number
  default     = 4096

  validation {
    condition     = var.ram_mb % 1024 == 0
    error_message = "RAM must be a multiple of 1024 MB."
  }
}

variable "disk_mb" {
  description = "System disk size in MB."
  type        = number
  default     = 30720
}

variable "disk_type" {
  description = "Disk type: ssd, nvme, hdd."
  type        = string
  default     = "nvme"
}
