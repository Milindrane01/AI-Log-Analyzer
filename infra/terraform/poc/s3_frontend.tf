# OPTIONAL (Phase 4): S3 static-website bucket for the React frontend.
# Disabled by default (enable_s3_frontend = false) because the basic POC serves
# the frontend from the Nginx container on EC2.
#
# NOTE: public S3 website hosting is fine for a POC but for anything real put
# CloudFront + OAC in front and keep the bucket private.

resource "aws_s3_bucket" "frontend" {
  count         = var.enable_s3_frontend ? 1 : 0
  bucket_prefix = "${var.project_name}-frontend-"
  force_destroy = true
}

resource "aws_s3_bucket_website_configuration" "frontend" {
  count  = var.enable_s3_frontend ? 1 : 0
  bucket = aws_s3_bucket.frontend[0].id
  index_document { suffix = "index.html" }
  # SPA fallback so client-side routes resolve
  error_document { key = "index.html" }
}

resource "aws_s3_bucket_public_access_block" "frontend" {
  count                   = var.enable_s3_frontend ? 1 : 0
  bucket                  = aws_s3_bucket.frontend[0].id
  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_policy" "frontend" {
  count  = var.enable_s3_frontend ? 1 : 0
  bucket = aws_s3_bucket.frontend[0].id
  depends_on = [aws_s3_bucket_public_access_block.frontend]
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "PublicReadForWebsite"
      Effect    = "Allow"
      Principal = "*"
      Action    = "s3:GetObject"
      Resource  = "${aws_s3_bucket.frontend[0].arn}/*"
    }]
  })
}
