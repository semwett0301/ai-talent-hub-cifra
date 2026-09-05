locals {
  app_dir = "/opt/${var.APP_NAME}"
}

resource "digitalocean_ssh_key" "deploy" {
  name       = "${var.APP_NAME}-deploy"
  public_key = trimspace(var.SSH_PUBLIC_KEY)
}

resource "digitalocean_droplet" "app" {
  name       = var.SERVER_NAME
  region     = var.REGION
  size       = var.SIZE
  image      = var.IMAGE
  ssh_keys   = [digitalocean_ssh_key.deploy.fingerprint]
  monitoring = true
  tags       = [var.APP_NAME]

  # Any cloud-init change replaces the droplet (user_data is immutable on DO).
  user_data = templatefile("${path.module}/cloud-init/cloud-init.yaml.tftpl", {
    app_dir        = local.app_dir
    hostname       = var.SERVER_NAME
    deploy_user    = var.DEPLOY_USER
    ssh_public_key = trimspace(var.SSH_PUBLIC_KEY)
  })
}

# Survives droplet replacement, so the deploy target address stays stable.
resource "digitalocean_reserved_ip" "app" {
  region     = var.REGION
  droplet_id = digitalocean_droplet.app.id
}
