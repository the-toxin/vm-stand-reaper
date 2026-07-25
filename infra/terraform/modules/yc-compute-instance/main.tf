data "yandex_compute_image" "this" {
  folder_id = var.image_folder_id
  name      = var.image_name
  family    = var.image_name == "" ? var.image_family : null
}

data "yandex_vpc_subnet" "main" {
  subnet_id = var.subnet_id
  folder_id = var.folder_id
}

resource "yandex_compute_instance" "this" {
  count                     = var.instance_count
  name                      = "${var.env}-${var.name}-${count.index + 1}"
  hostname                  = "${var.env}-${var.name}-${count.index + 1}"
  folder_id                 = var.folder_id
  labels                    = var.labels

  zone                      = data.yandex_vpc_subnet.main.zone
  platform_id               = var.platform_id
  allow_stopping_for_update = var.allow_stopping_for_update
  network_acceleration_type = var.network_acceleration_type
  service_account_id        = var.service_account_id

  resources {
    cores         = var.cores
    memory        = var.memory
    core_fraction = var.core_fraction
  }

  scheduling_policy {
    preemptible = var.scheduling_policy_preemptible
  }

  boot_disk {
    initialize_params {
      name        = "${var.env}-${var.name}-${count.index + 1}-boot-disk"
      image_id    = var.snapshot_id == "" ? (var.image_id == "" ? data.yandex_compute_image.this.id : var.image_id) : ""
      snapshot_id = var.snapshot_id
      size        = var.boot_disk_size
      type        = var.boot_disk_type
    }
  }

  network_interface {
    subnet_id          = data.yandex_vpc_subnet.main.id
    ip_address         = length(var.ip_addresses) > count.index ? var.ip_addresses[count.index] : ""
    nat                = var.nat
    security_group_ids = var.security_group_ids
  }

  metadata = {
    role      = "${var.env}-${var.name}"
    zone      = data.yandex_vpc_subnet.main.zone
    ssh-keys  = var.cloud_init_file == "" ? (var.ssh_keys != "" ? var.ssh_keys : null) : null
    user-data = var.cloud_init_file != "" ? file(var.cloud_init_file) : null
  }

  timeouts {
    create = var.timeout_create
    update = var.timeout_update
    delete = var.timeout_delete
  }
}

resource "local_file" "ansible_inventory" {
  count = var.ansible_inventory_group != "" ? 1 : 0
  depends_on = [
    yandex_compute_instance.this,
  ]
  content = templatefile("inventory.tftpl", {
    "group"         = var.ansible_inventory_group,
    "names"         = yandex_compute_instance.this.*.hostname,
    "ansible_hosts" = yandex_compute_instance.this.*.network_interface.0.ip_address
  })
  filename        = "${var.ansible_inventory_dir}/${var.env}-${var.name}-inventory.yaml"
  file_permission = "0664"
}
