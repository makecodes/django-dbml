from django.core.management import call_command
import pytest


@pytest.mark.django_db
def test_default_model(capfd):
    call_command("dbml")
    out, err = capfd.readouterr()
    with open("tests/examples/test0.dbml", "r") as f:
        expected = f.read()
    print(out)
    assert out == expected