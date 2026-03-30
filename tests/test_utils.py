from django_dbml.utils import to_snake_case


def test_to_snake_case_preserves_common_initialisms() -> None:
    assert to_snake_case("GenericIPAddressField") == "generic_ip_address_field"
    assert to_snake_case("UUIDField") == "uuid_field"
    assert to_snake_case("URLField") == "url_field"
    assert to_snake_case("JSONField") == "json_field"
