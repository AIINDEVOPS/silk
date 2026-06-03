output "bucket_name" {
  value = aws_s3_bucket.csv_uploads.bucket
}

output "bucket_arn" {
  value = aws_s3_bucket.csv_uploads.arn
}

output "bucket_region" {
  value = aws_s3_bucket.csv_uploads.region
}

output "iam_role_arn" {
  value = aws_iam_role.csv_app_role.arn
}
