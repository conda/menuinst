""""""

from conftest import DATA


def test_install():
    from menuinst.api import install

    install(DATA / "example-1.json")
