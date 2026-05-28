variable "project_id" {
  description = "GCP project ID"
  type        = string
  default     = "stella-cyber-analyzer"
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "image_tag" {
  description = "Docker image tag to deploy"
  type        = string
  default     = "latest"
}
