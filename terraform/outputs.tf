output "server_ipv4" {
  description = "Reserved public IPv4 of the droplet (stable across replacements)."
  value       = digitalocean_reserved_ip.app.ip_address
}

output "ssh_command" {
  description = "Ready-to-use SSH command."
  value       = "ssh -i ~/.ssh/deploy_key ${var.DEPLOY_USER}@${digitalocean_reserved_ip.app.ip_address}"
}

output "app_url" {
  description = "Application URL (HTTP, by IP)."
  value       = "http://${digitalocean_reserved_ip.app.ip_address}"
}
