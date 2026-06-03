terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  backend "s3" {
    bucket = "terraform-state-devops-case-study"
    key    = "s3/terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region
}

# ── S3 Bucket for CSV uploads ───────────────────────────────────────────────
resource "aws_s3_bucket" "csv_uploads" {
  bucket = var.bucket_name
  tags   = local.common_tags
}

resource "aws_s3_bucket_versioning" "csv_uploads" {
  bucket = aws_s3_bucket.csv_uploads.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "csv_uploads" {
  bucket = aws_s3_bucket.csv_uploads.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "csv_uploads" {
  bucket                  = aws_s3_bucket.csv_uploads.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ── S3 Lifecycle: Standard → Standard-IA → Glacier → Delete ─────────────────
resource "aws_s3_bucket_lifecycle_configuration" "csv_uploads" {
  bucket = aws_s3_bucket.csv_uploads.id

  rule {
    id     = "processed-csv-lifecycle"
    status = "Enabled"

    filter {
      prefix = "processed/"
    }

    # Move to Standard-IA after 30 days (lower cost, slightly slower access)
    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    # Move to S3 Glacier Instant Retrieval after 90 days
    transition {
      days          = 90
      storage_class = "GLACIER_IR"
    }

    # Move to S3 Glacier Flexible Retrieval after 180 days (cheapest archive)
    transition {
      days          = 180
      storage_class = "GLACIER"
    }

    # Move to S3 Glacier Deep Archive after 365 days (lowest cost long-term)
    transition {
      days          = 365
      storage_class = "DEEP_ARCHIVE"
    }

    # Delete objects after 7 years (compliance retention)
    expiration {
      days = 2555
    }

    # Clean up incomplete multipart uploads after 7 days
    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }

  rule {
    id     = "noncurrent-version-cleanup"
    status = "Enabled"

    filter {
      prefix = ""
    }

    noncurrent_version_transition {
      noncurrent_days = 30
      storage_class   = "GLACIER"
    }

    noncurrent_version_expiration {
      noncurrent_days = 365
    }
  }

  rule {
    id     = "uploads-cleanup"
    status = "Enabled"

    filter {
      prefix = "uploads/"
    }

    # Clean up raw uploads after 7 days (already moved to processed/)
    expiration {
      days = 7
    }
  }
}

# ── S3 CORS for web uploads ─────────────────────────────────────────────────
resource "aws_s3_bucket_cors_configuration" "csv_uploads" {
  bucket = aws_s3_bucket.csv_uploads.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "PUT", "POST"]
    allowed_origins = var.allowed_origins
    max_age_seconds = 3000
  }
}

# ── IAM Role for the application (IRSA / EC2 instance profile) ───────────────
resource "aws_iam_role" "csv_app_role" {
  name = "csv-app-s3-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
  tags = local.common_tags
}

resource "aws_iam_role_policy" "csv_app_s3_policy" {
  name = "csv-app-s3-access"
  role = aws_iam_role.csv_app_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket",
          "s3:DeleteObject"
        ]
        Resource = [
          aws_s3_bucket.csv_uploads.arn,
          "${aws_s3_bucket.csv_uploads.arn}/*"
        ]
      }
    ]
  })
}

locals {
  common_tags = {
    Project     = "devops-case-study"
    ManagedBy   = "terraform"
    Environment = var.environment
  }
}
