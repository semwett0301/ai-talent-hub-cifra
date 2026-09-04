# ---- Deploy / app ----
variable "SSH_PUBLIC_KEY" {
  description = "Public SSH key (OpenSSH format) installed for root and the deploy user."
  type        = string
  sensitive   = true
}

variable "DEPLOY_USER" {
  description = "Non-root user created on the server for SSH/deploy."
  type        = string
  default     = "deploy"
}

variable "SERVER_NAME" {
  description = "Droplet name (also its hostname)."
  type        = string
  default     = "cifra-prod"
}

variable "APP_NAME" {
  description = "Project slug: /opt/<app_name>, SSH key name, firewall name, tag."
  type        = string
  default     = "cifra"
}

# ---- Droplet ----
variable "REGION" {
  description = "Droplet region slug, e.g. ams3, fra1."
  type        = string
  default     = "ams3"
}

variable "SIZE" {
  description = "Droplet size slug (`doctl compute size list`)."
  type        = string
  default     = "s-2vcpu-4gb"
}

variable "IMAGE" {
  description = "Droplet image slug (`doctl compute image list-distribution`)."
  type        = string
  default     = "ubuntu-24-04-x64"
}
