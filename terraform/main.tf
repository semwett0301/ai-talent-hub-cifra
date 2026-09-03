locals {
  app_dir         = "/opt/${var.APP_NAME}"
  server_hostname = replace(replace(var.APP_NAME, ".", "-"), "_", "-")
}

data "twc_configurator" "main" {
  location  = var.LOCATION
  disk_type = var.DISK_TYPE
}

data "twc_software" "docker" {
  name = "Docker"

  os {
    family  = "linux"
    name    = var.OS_NAME
    version = var.OS_VERSION
  }
}

resource "twc_ssh_key" "deploy" {
  name = "${var.APP_NAME}-deploy"
  body = var.SSH_PUBLIC_KEY
}

resource "twc_floating_ip" "app" {
  availability_zone = var.AVAILABILITY_ZONE
}

resource "twc_server" "app" {
  name     = var.SERVER_NAME
  hostname = local.server_hostname

  os_id       = data.twc_software.docker.os[0].id
  software_id = data.twc_software.docker.id

  availability_zone = var.AVAILABILITY_ZONE
  floating_ip_id    = twc_floating_ip.app.id

  configuration {
    configurator_id = data.twc_configurator.main.id
    cpu             = var.CPU
    ram             = var.RAM_MB
    disk            = var.DISK_MB
  }

  ssh_keys_ids = [twc_ssh_key.deploy.id]

  is_root_password_required = false

  cloud_init = templatefile("${path.module}/cloud-init/cloud-init.yaml.tftpl", {
    app_dir        = local.app_dir
    hostname       = local.server_hostname
    deploy_user    = var.DEPLOY_USER
    ssh_public_key = trimspace(var.SSH_PUBLIC_KEY)
  })

  lifecycle {
    # os_id/software_id are resolved from data.twc_software each plan; freeze them
    # (and cloud_init, first-boot only) so image-id drift never reinstalls the server.
    ignore_changes = [cloud_init, os_id, software_id]
  }
}

