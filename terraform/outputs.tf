output "server_ipv4" {
  description = "Public IPv4 of the server (main interface)."
  value       = twc_server.app.main_ipv4
}

output "ssh_command" {
  description = "Ready-to-use SSH command."
  value       = "ssh -i ~/.ssh/timeweb_deploy root@${twc_server.app.main_ipv4}"
}

output "app_url" {
  description = "Application URL (HTTP, by IP)."
  value       = "http://${twc_server.app.main_ipv4}"
}
