from services.ip_location_service import lookup_ip_locations


def test_lookup_ip_locations_labels_private_ip():
    locations = lookup_ip_locations(["192.168.1.10"])

    assert locations["192.168.1.10"].location == "内网地址"
    assert locations["192.168.1.10"].source == "local"
