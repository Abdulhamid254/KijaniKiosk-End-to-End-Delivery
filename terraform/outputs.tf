output "staging_namespace_name" {
  value       = kubernetes_namespace.staging.metadata[0].name
  description = "The verified, parameterized execution boundary for staging."
}

output "production_namespace_name" {
  value       = kubernetes_namespace.production.metadata[0].name
  description = "The target cluster namespace simulation layer where production runtime processes execute."
}
