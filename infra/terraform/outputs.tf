output "service_url" {
  description = "JuaKazi Cloud Run service URL"
  value       = google_cloud_run_v2_service.juakazi.uri
}

output "registry_url" {
  description = "Artifact Registry URL for Docker images"
  value       = "${local.registry_host}/${var.project_id}/juakazi"
}
