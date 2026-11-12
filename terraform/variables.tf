variable "kube_config_path" {
  type        = string
  default     = "~/.kube/config"
  description = "The localized filesystem path mapping out our cluster certificate credentials context."
}

variable "staging_namespace_name" {
  type        = string
  default     = "kijani-staging"
  description = "The operational workspace isolation identifier assigned to our staging environment."
}

variable "production_namespace_name" {
  type        = string
  default     = "default"
  description = "The target cluster namespace simulation layer where production runtime processes execute."
}
