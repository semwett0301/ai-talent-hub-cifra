output "server_ipv4" {
  description = "Public IPv4 of the server (added via twc_server_ip)."
  value       = twc_server_ip.ipv4.ip
}

output "ssh_command" {
  description = "Ready-to-use SSH command."
  value       = "ssh -i ~/.ssh/timeweb_deploy root@${twc_server_ip.ipv4.ip}"
}

output "app_url" {
  description = "Application URL (HTTP, by IP)."
  value       = "http://${twc_server_ip.ipv4.ip}"
}
