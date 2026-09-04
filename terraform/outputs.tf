output "server_ipv4" {
  description = "Public IPv4 of the instance."
  value       = oci_core_instance.app.public_ip
}

output "ssh_command" {
  description = "Ready-to-use SSH command."
  value       = "ssh -i ~/.ssh/deploy_key ${var.DEPLOY_USER}@${oci_core_instance.app.public_ip}"
}

output "app_url" {
  description = "Application URL (HTTP, by IP)."
  value       = "http://${oci_core_instance.app.public_ip}"
}
