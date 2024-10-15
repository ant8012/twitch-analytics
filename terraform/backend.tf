# Backend is set via github workflow
terraform {
  backend "s3" {
    bucket = "placholder-bucket"
    key    = "path/terraform.tfstate"
    region = "us-east-1"
  }
}
