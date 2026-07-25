terraform {
  source = "../../../../terraform/modules/yc-compute-instance"
}

include {
  path = find_in_parent_folders("root.hcl")
}

locals {
  environment_vars = read_terragrunt_config(find_in_parent_folders("env.hcl"))
  folder_id        = local.environment_vars.locals.folder_id
  subnet_id        = local.environment_vars.locals.subnet_id
  env              = local.environment_vars.locals.env
}

inputs = {
  folder_id                     = local.folder_id
  subnet_id                     = local.subnet_id
  env                           = local.env
  name                          = "app"
  instance_count                = 1
  scheduling_policy_preemptible = true
  platform_id                   = "standard-v2"
  cores                         = 2
  core_fraction                 = 5
  memory                        = 1
  boot_disk_size                = 10
  image_family                  = "ubuntu-2404-lts"
  ssh_keys                      = file("~/.ssh/dev_env.pub")
  labels                        = yamldecode(file(find_in_parent_folders("labels.yaml")))
}
