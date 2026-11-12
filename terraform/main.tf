terraform {
  required_version = ">= 1.7"
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
  }
}

# Authenticates against our parameter-driven cluster configuration path
provider "kubernetes" {
  config_path = var.kube_config_path
}

# Provision the production-isolated staging workspace using variable tags
resource "kubernetes_namespace" "staging" {
  metadata {
    name = var.staging_namespace_name
    labels = {
      environment = "staging"
      managed-by  = "terraform"
    }
  }
}

# Tells Terraform to adopt the pre-existing default namespace safely
import {
  to = kubernetes_namespace.production
  id = "default"
}

# Provision the default production workspace simulation using variable tags
resource "kubernetes_namespace" "production" {
  metadata {
    name = var.production_namespace_name
    labels = {
      environment = "production"
      managed-by  = "terraform"
    }
  }
}
