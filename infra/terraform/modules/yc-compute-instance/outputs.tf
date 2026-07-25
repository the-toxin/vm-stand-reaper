output "list_of_nodes" {
  description = "List of \"Hostname\"-\"IP address\"-\"Zone\""
  value = [
    for key, value in yandex_compute_instance.this :
    {
      "name"       = value.name,
      "ip_address" = value.network_interface.0.ip_address,
      "zone"       = value.zone
    }
  ]
}
