# Multi-cloud infrastructure for OpenDistillery
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.20"
    }
  }
}

# Configure providers
provider "aws" {
  region = var.aws_region
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

provider "azurerm" {
  features {}
}

# Variables
variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-west-2"
}

variable "gcp_project_id" {
  description = "GCP project ID"
  type        = string
}

variable "gcp_region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

# AWS Infrastructure
module "aws_infrastructure" {
  source = "./modules/aws"
  
  environment = var.environment
  region      = var.aws_region
  
  # ECS Configuration
  ecs_cluster_name = "opendistillery-${var.environment}"
  ecs_service_desired_count = 3
  
  # RDS Configuration
  rds_instance_class = "db.r5.xlarge"
  rds_allocated_storage = 100
  rds_multi_az = true
  
  # ElastiCache Configuration
  elasticache_node_type = "cache.r5.large"
  elasticache_num_cache_nodes = 2
  
  # Application Load Balancer
  alb_certificate_arn = var.aws_certificate_arn
  
  tags = {
    Environment = var.environment
    Project     = "OpenDistillery"
    ManagedBy   = "Terraform"
  }
}

# GCP Infrastructure
module "gcp_infrastructure" {
  source = "./modules/gcp"
  
  project_id  = var.gcp_project_id
  region      = var.gcp_region
  environment = var.environment
  
  # GKE Configuration
  gke_cluster_name = "opendistillery-${var.environment}"
  gke_node_count = 3
  gke_machine_type = "e2-standard-4"
  
  # Cloud SQL Configuration
  cloudsql_tier = "db-standard-2"
  cloudsql_disk_size = 100
  cloudsql_availability_type = "REGIONAL"
  
  # Redis Configuration
  redis_memory_size_gb = 4
  redis_tier = "STANDARD_HA"
}

# Azure Infrastructure
module "azure_infrastructure" {
  source = "./modules/azure"
  
  environment = var.environment
  location    = "East US"
  
  # AKS Configuration
  aks_cluster_name = "opendistillery-${var.environment}"
  aks_node_count = 3
  aks_vm_size = "Standard_D4s_v3"
  
  # PostgreSQL Configuration
  postgresql_sku_name = "GP_Standard_D4s_v3"
  postgresql_storage_mb = 102400
  
  # Redis Configuration
  redis_family = "P"
  redis_sku_name = "Premium"
  redis_capacity = 1
}

# Global CDN and DNS
resource "aws_cloudfront_distribution" "global_cdn" {
  origin {
    domain_name = module.aws_infrastructure.alb_dns_name
    origin_id   = "opendistillery-origin"
    
    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }
  
  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"
  
  default_cache_behavior {
    allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "opendistillery-origin"
    compress               = true
    viewer_protocol_policy = "redirect-to-https"
    
    forwarded_values {
      query_string = true
      headers      = ["Authorization", "Content-Type"]
      cookies {
        forward = "none"
      }
    }
    
    min_ttl     = 0
    default_ttl = 3600
    max_ttl     = 86400
  }
  
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }
  
  viewer_certificate {
    acm_certificate_arn      = var.aws_certificate_arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }
  
  tags = {
    Environment = var.environment
    Project     = "OpenDistillery"
  }
}

# Monitoring and Observability
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "OpenDistillery-${var.environment}"
  
  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        
        properties = {
          metrics = [
            ["AWS/ECS", "CPUUtilization", "ClusterName", module.aws_infrastructure.ecs_cluster_name],
            ["AWS/ECS", "MemoryUtilization", "ClusterName", module.aws_infrastructure.ecs_cluster_name]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "ECS Cluster Metrics"
        }
      }
    ]
  })
}

# Output important values
output "aws_alb_dns_name" {
  description = "AWS Application Load Balancer DNS name"
  value       = module.aws_infrastructure.alb_dns_name
}

output "gcp_cluster_endpoint" {
  description = "GCP GKE cluster endpoint"
  value       = module.gcp_infrastructure.cluster_endpoint
  sensitive   = true
}

output "azure_cluster_fqdn" {
  description = "Azure AKS cluster FQDN"
  value       = module.azure_infrastructure.cluster_fqdn
}

output "cloudfront_domain_name" {
  description = "CloudFront distribution domain name"
  value       = aws_cloudfront_distribution.global_cdn.domain_name
}