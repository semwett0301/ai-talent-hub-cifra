locals {
  app_dir         = "/opt/${var.APP_NAME}"
  server_hostname = replace(replace(var.APP_NAME, ".", "-"), "_", "-")
}

data "oci_identity_availability_domains" "ads" {
  compartment_id = var.OCI_TENANCY_OCID
}

# Newest Ubuntu image matching the shape's architecture (A1.Flex -> aarch64).
data "oci_core_images" "ubuntu" {
  compartment_id           = var.OCI_COMPARTMENT_OCID
  operating_system         = var.OS
  operating_system_version = var.OS_VERSION
  shape                    = var.SHAPE
  sort_by                  = "TIMECREATED"
  sort_order               = "DESC"
}

resource "oci_core_instance" "app" {
  compartment_id      = var.OCI_COMPARTMENT_OCID
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
  display_name        = var.SERVER_NAME
  shape               = var.SHAPE

  shape_config {
    ocpus         = var.OCPUS
    memory_in_gbs = var.MEMORY_GB
  }

  source_details {
    source_type             = "image"
    source_id               = data.oci_core_images.ubuntu.images[0].id
    boot_volume_size_in_gbs = var.BOOT_VOLUME_GB
  }

  create_vnic_details {
    subnet_id        = oci_core_subnet.app.id
    assign_public_ip = true
    hostname_label   = local.server_hostname
  }

  metadata = {
    ssh_authorized_keys = var.SSH_PUBLIC_KEY
    user_data = base64encode(templatefile("${path.module}/cloud-init/cloud-init.yaml.tftpl", {
      app_dir        = local.app_dir
      hostname       = local.server_hostname
      deploy_user    = var.DEPLOY_USER
      ssh_public_key = trimspace(var.SSH_PUBLIC_KEY)
    }))
  }

  lifecycle {
    # Image drift shouldn't recreate the box; a cloud-init edit should reprovision.
    ignore_changes = [source_details[0].source_id]
  }
}
