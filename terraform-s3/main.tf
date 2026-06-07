terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  # Local state — no remote backend required to run this
  # To use remote state, uncomment and configure:
  # backend "s3" {
  #   bucket = "your-terraform-state-bucket"
  #   key    = "s3/terraform.tfstate"
  #   region = "us-east-1"
  # }
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

# ── S3 Glacier Transition — as required by the assignment ────────────────────
#
# Assignment requirement: "Waiting you to implement s3 glacier transition on s3 config"
#
# Lifecycle flow for processed CSV files:
#
#   Day 0    Upload        →  STANDARD         (full performance, instant access)
#   Day 30   Transition    →  STANDARD_IA      (~40% cheaper, infrequent access)
#   Day 90   Transition    →  GLACIER_IR       (~68% cheaper, millisecond retrieval)
#   Day 180  Transition    →  GLACIER          (~80% cheaper, 3-5 hour retrieval)
#   Day 365  Transition    →  DEEP_ARCHIVE     (~95% cheaper, 12 hour retrieval)
#   Day 2555 Expiration    →  DELETE           (7-year compliance retention window)
#
resource "aws_s3_bucket_lifecycle_configuration" "csv_uploads" {
  bucket = aws_s3_bucket.csv_uploads.id

  # Rule 1: Glacier transition for processed CSV files
  rule {
    id     = "csv-glacier-transition"
    status = "Enabled"

    filter {
      prefix = "processed/"
    }

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 90
      storage_class = "GLACIER_IR"
    }

    transition {
      days          = 180
      storage_class = "GLACIER"
    }

    transition {
      days          = 365
      storage_class = "DEEP_ARCHIVE"
    }

    expiration {
      days = 2555
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }

  # Rule 2: Clean up raw upload temp files after 7 days
  rule {
    id     = "uploads-temp-cleanup"
    status = "Enabled"

    filter {
      prefix = "uploads/"
    }

    expiration {
      days = 7
    }
  }

  # Rule 3: Move non-current (versioned) objects to Glacier and expire after 1 year
  rule {
    id     = "noncurrent-version-lifecycle"
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
