terraform {
  required_version = ">= 1.6"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

locals {
  registry_host = "${var.region}-docker.pkg.dev"
  image_name    = "${local.registry_host}/${var.project_id}/juakazi/juakazi:${var.image_tag}"
}

resource "google_project_service" "cloud_run" {
  service            = "run.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "artifact_registry" {
  service            = "artifactregistry.googleapis.com"
  disable_on_destroy = false
}

resource "google_artifact_registry_repository" "juakazi" {
  location      = var.region
  repository_id = "juakazi"
  format        = "DOCKER"
  depends_on    = [google_project_service.artifact_registry]
}

data "google_project" "project" {
  project_id = var.project_id
}

resource "google_cloud_run_v2_service" "juakazi" {
  name     = "juakazi"
  location = var.region

  template {
    scaling {
      min_instance_count = 0
      max_instance_count = 3
    }
    containers {
      image = local.image_name

      resources {
        limits = {
          cpu    = "1"
          memory = "4Gi"
        }
      }

      env {
        name  = "ENVIRONMENT"
        value = "production"
      }

      ports {
        container_port = 8000
      }

      liveness_probe {
        http_get {
          path = "/health"
        }
        initial_delay_seconds = 15
        period_seconds        = 30
      }
    }
  }

  depends_on = [
    google_project_service.cloud_run,
    google_artifact_registry_repository.juakazi,
  ]
}

resource "google_cloud_run_v2_service_iam_member" "public_invoker" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.juakazi.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
