locals {
  app_dir         = "/opt/${var.app_name}"
  server_hostname = replace(replace(var.app_name, ".", "-"), "_", "-")
}

data "twc_configurator" "main" {
  location  = var.location
  disk_type = var.disk_type
}

data "twc_software" "docker" {
  name = "Docker"

  os {
    family  = "linux"
    name    = var.os_name
    version = var.os_version
  }
}

data "twc_ssh_keys" "deploy" {
  name = var.ssh_key_name
}

resource "twc_server" "app" {
  name     = var.server_name
  hostname = local.server_hostname

  os_id       = data.twc_software.docker.os[0].id
  software_id = data.twc_software.docker.id

  availability_zone = var.availability_zone

  configuration {
    configurator_id = data.twc_configurator.main.id
    cpu             = var.cpu
    ram             = var.ram_mb
    disk            = var.disk_mb
  }

  ssh_keys_ids = [data.twc_ssh_keys.deploy.id]

  is_root_password_required = false

  cloud_init = templatefile("${path.module}/cloud-init/cloud-init.yaml.tftpl", {
    app_dir        = local.app_dir
    hostname       = local.server_hostname
    ssh_public_key = trimspace(data.twc_ssh_keys.deploy.body)
  })

  lifecycle {
    # os_id/software_id are resolved from data.twc_software each plan; freeze them
    # (and cloud_init, first-boot only) so image-id drift never reinstalls the server.
    ignore_changes = [cloud_init, os_id, software_id]
  }
}
