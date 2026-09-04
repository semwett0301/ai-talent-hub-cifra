# Public networking: VCN -> internet gateway -> route table -> subnet, with a
# security list opening only 22 (SSH) and 80 (HTTP).

resource "oci_core_vcn" "app" {
  compartment_id = var.OCI_COMPARTMENT_OCID
  cidr_blocks    = ["10.0.0.0/16"]
  display_name   = "${var.APP_NAME}-vcn"
  dns_label      = "app"
}

resource "oci_core_internet_gateway" "app" {
  compartment_id = var.OCI_COMPARTMENT_OCID
  vcn_id         = oci_core_vcn.app.id
  display_name   = "${var.APP_NAME}-igw"
}

resource "oci_core_route_table" "app" {
  compartment_id = var.OCI_COMPARTMENT_OCID
  vcn_id         = oci_core_vcn.app.id
  display_name   = "${var.APP_NAME}-rt"

  route_rules {
    destination       = "0.0.0.0/0"
    network_entity_id = oci_core_internet_gateway.app.id
  }
}

resource "oci_core_security_list" "app" {
  compartment_id = var.OCI_COMPARTMENT_OCID
  vcn_id         = oci_core_vcn.app.id
  display_name   = "${var.APP_NAME}-sl"

  egress_security_rules {
    destination = "0.0.0.0/0"
    protocol    = "all"
  }

  ingress_security_rules {
    protocol = "6" # TCP
    source   = "0.0.0.0/0"
    tcp_options {
      min = 22
      max = 22
    }
  }

  ingress_security_rules {
    protocol = "6" # TCP
    source   = "0.0.0.0/0"
    tcp_options {
      min = 80
      max = 80
    }
  }
}

resource "oci_core_subnet" "app" {
  compartment_id             = var.OCI_COMPARTMENT_OCID
  vcn_id                     = oci_core_vcn.app.id
  cidr_block                 = "10.0.1.0/24"
  display_name               = "${var.APP_NAME}-subnet"
  route_table_id             = oci_core_route_table.app.id
  security_list_ids          = [oci_core_security_list.app.id]
  prohibit_public_ip_on_vnic = false
  dns_label                  = "app"
}
