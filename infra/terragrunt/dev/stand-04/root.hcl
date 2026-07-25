locals {
  cloud_vars       = read_terragrunt_config(find_in_parent_folders("cloud.hcl"))
  cloud_id         = local.cloud_vars.locals.cloud_id
  state_bucket     = local.cloud_vars.locals.state_bucket
  environment_vars = read_terragrunt_config(find_in_parent_folders("env.hcl"))
  env              = local.environment_vars.locals.env
}

# Don't use in production!
# Not recommended use local states. Only for test runs!
remote_state {
  backend = "local"
  generate = {
    path      = "backend.tf"
    if_exists = "overwrite"
  }
  config = {
    path = "${get_env("HOME")}/.cache/terraform/${local.state_bucket}/${local.env}/${path_relative_to_include()}/terraform.tfstate"
  }
}

# remote_state {
#   backend = "s3"
#   generate = {
#     path      = "backend.tf"
#     if_exists = "overwrite_terragrunt"
#   }
#   config = {
#     endpoint                           = "https://storage.yandexcloud.net"
#     bucket                             = "${local.state_bucket}"
#     region                             = "us-east-1"
#     key                                = "${local.env}/${path_relative_to_include()}/terraform.tfstate"
#     skip_region_validation             = true
#     skip_credentials_validation        = true
#     skip_bucket_versioning             = true
#     skip_bucket_ssencryption           = true
#     skip_bucket_root_access            = true
#     skip_bucket_enforced_tls           = true
#     skip_bucket_public_access_blocking = true
#   }
# }

generate "provider" {
  path      = "provider.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<EOF

provider "yandex" {
     cloud_id  = "${local.cloud_id}"
   }

EOF
}
