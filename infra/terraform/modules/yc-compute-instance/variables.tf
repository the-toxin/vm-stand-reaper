variable "folder_id" {
  description = "Folder that the resource belongs to"
  type        = string
}
variable "subnet_id" {
  description = "ID of the subnet to attach this interface to"
  type        = string
}
variable "env" {
  description = "Environment/Project name. Used as resources naming prefix"
  type        = string
}
variable "instance_count" {
  description = "Compute instance count"
  type        = number
}
variable "name" {
  description = "Compute instance name"
  type        = string
}
variable "labels" {
  default     = {}
  description = "A set of labels which will be applied to all resources"
  type        = map(string)
}
variable "cores" {
  description = "CPU cores for the instance"
  type        = number
}
variable "memory" {
  description = "Memory size in GB"
  type        = number
}
variable "core_fraction" {
  default     = "100"
  description = "If provided, specifies baseline performance for a core as a percent"
  type        = number
}
variable "platform_id" {
  default     = "standard-v3"
  description = "The type of virtual machine to create. For details: https://cloud.yandex.ru/docs/compute/concepts/vm-platforms"
  type        = string
}
variable "allow_stopping_for_update" {
  default     = false
  description = "If true, allows Terraform to stop the instance in order to update its properties. If you try to update a property that requires stopping the instance without setting this field, the update will fail"
  type        = bool
}
variable "scheduling_policy_preemptible" {
  default     = false
  description = "Specifies if the instance is preemptible. For details: https://cloud.yandex.ru/docs/compute/concepts/preemptible-vm"
  type        = bool
}
variable "network_acceleration_type" {
  default     = "standard"
  description = "Type of network acceleration. The default is standard. Values: standard, software_accelerated"
  type        = string
}
variable "ip_addresses" {
  default     = []
  description = "List of private IP addresses to be assigned by instances. If list item is an empty string, the address will be automatically assigned from the specified subnet"
  type        = list(string)
}
variable "nat" {
  default     = false
  description = "Provide a public address, for instance, to access the internet over NAT"
  type        = bool
}
variable "security_group_ids" {
  default     = []
  description = "Security group ids for network interface"
  type        = list(string)
}
variable "service_account_id" {
  default     = ""
  description = "ID of the service account authorized for this instance. For details: https://cloud.yandex.ru/docs/iam/concepts/users/service-accounts"
  type        = string
}
variable "image_id" {
  default     = ""
  description = "A disk image to initialize this disk from. Either \"image_id\" or \"snapshot_id\" must be specified"
  type        = string
}
variable "snapshot_id" {
  default     = ""
  description = "A snapshot to initialize this disk from"
  type        = string
}
variable "image_folder_id" {
  default     = ""
  description = "Folder that the resource belongs to. If value is omitted, the default provider folder is used"
  type        = string
}
variable "image_name" {
  default     = ""
  description = "The name of an image. Used to search the image_id by name"
  type        = string
}
variable "image_family" {
  default     = "ubuntu-2204-lts"
  description = "The family name of an image. Used to search the latest image_id in a family"
  type        = string
}
variable "boot_disk_size" {
  description = "The boot disk parameter for the instance. Size of the disk in GB"
  type        = number
}
variable "boot_disk_type" {
  default     = "network-hdd"
  description = "The boot disk parameter for the instance. Disk type. For details: https://cloud.yandex.ru/docs/compute/concepts/disk#disks_types"
  type        = string
}
variable "cloud_init_file" {
  default     = ""
  description = "Path to the Cloud-init file. For details: https://cloud.yandex.ru/docs/compute/concepts/vm-metadata#keys-processed-in-public-images"
  type        = string
}
variable "ssh_keys" {
  default     = ""
  description = "The key for SSH-key delivery to Linux VM. For details: https://cloud.yandex.ru/docs/compute/concepts/vm-metadata#keys-processed-in-public-images"
  type        = string
}
variable "timeout_create" {
  default     = "5m"
  description = "Create operation timeout. For details: https://developer.hashicorp.com/terraform/language/resources/syntax#operation-timeouts"
  type        = string
}
variable "timeout_update" {
  default     = "5m"
  description = "Update operation timeout. For details: https://developer.hashicorp.com/terraform/language/resources/syntax#operation-timeouts"
  type        = string
}
variable "timeout_delete" {
  default     = "5m"
  description = "Delete operation timeout. For details: https://developer.hashicorp.com/terraform/language/resources/syntax#operation-timeouts"
  type        = string
}
variable "ansible_inventory_group" {
  default     = ""
  description = "The group of managed hosts in the ansible inventory file"
  type        = string
}
variable "ansible_inventory_dir" {
  default     = "/tmp"
  description = "The directory that saves the ansible inventory file"
  type        = string
}
