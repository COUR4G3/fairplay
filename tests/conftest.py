from pathlib import Path

import pytest
from flask import Flask


@pytest.fixture
def app(request: pytest.FixtureRequest, tmp_path: Path):
    app = Flask(
        request.module.__name__, instance_path=str(tmp_path / "instance")
    )

    app.testing = True

    return app


@pytest.fixture
def app_context(app: Flask):
    with app.app_context() as ctx:
        yield ctx


def pytest_addoption(parser):
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="run integration tests",
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--integration"):
        # --integration given in cli: do not skip integration tests
        return
    skip_integration = pytest.mark.skip(
        reason="need --integration option to run"
    )
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)