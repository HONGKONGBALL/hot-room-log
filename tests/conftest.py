import pytest

from hotroom import create_app


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    database = tmp_path_factory.mktemp("hotroom") / "test.db"
    app = create_app(
        {
            "DATABASE": str(database),
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "READONLY": False,
        }
    )
    return app.test_client()
