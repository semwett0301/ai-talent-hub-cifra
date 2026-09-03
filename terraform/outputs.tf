output "server_id" {
  description = "Server ID in Timeweb Cloud."
  value       = twc_server.app.id
}

output "server_ipv4" {
  description = "Public IPv4 of the server."
  value       = twc_server.app.main_ipv4
}

output "server_status" {
  description = "Current server status (on, installing, software_install, ...)."
  value       = twc_server.app.status
}

output "ssh_command" {
  description = "Ready-to-use SSH command."
  value       = "ssh -i ~/.ssh/timeweb_deploy root@${twc_server.app.main_ipv4}"
}

output "app_url" {
  description = "Application URL (HTTP, by IP)."
  value       = "http://${twc_server.app.main_ipv4}"
}

output "root_password" {
  description = "Root password (empty when is_root_password_required = false)."
  value       = twc_server.app.root_pass
  sensitive   = true
}
