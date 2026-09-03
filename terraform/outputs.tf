output "server_ipv4" {
  description = "Public IPv4 of the server (floating IP)."
  value       = twc_floating_ip.app.ip
}

output "ssh_command" {
  description = "Ready-to-use SSH command."
  value       = "ssh -i ~/.ssh/timeweb_deploy root@${twc_floating_ip.app.ip}"
}

output "app_url" {
  description = "Application URL (HTTP, by IP)."
  value       = "http://${twc_floating_ip.app.ip}"
}
