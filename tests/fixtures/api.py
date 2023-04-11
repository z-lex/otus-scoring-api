from __future__ import annotations

import typing as t

import pytest
import redis
import redis.exceptions
import requests

if t.TYPE_CHECKING:
    from pytest_docker.plugin import Services


@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig: pytest.Config):
    return str(pytestconfig.rootpath / "../../docker-compose.yml")


@pytest.fixture(scope="session")
def api_url(docker_ip: str, docker_services: Services) -> str:
    def is_responsive(url: str) -> bool:
        try:
            response = requests.post(url)
            # must return BAD_REQUEST for empty post request
            if response.status_code == 400:
                return True
        except ConnectionError:
            return False

    port = docker_services.port_for("otus-scoring-api", 8080)
    url = f"http://{docker_ip}:{port}/method"
    docker_services.wait_until_responsive(
        timeout=30.0, pause=0.1, check=lambda: is_responsive(url)
    )
    return url


@pytest.fixture(scope="session")
def redis_instance(docker_ip: str, docker_services: Services) -> redis.Redis:
    def is_responsive(redis_inst: redis.Redis) -> bool:
        try:
            return redis_inst.ping()
        except (
            redis.exceptions.ConnectionError,
            redis.exceptions.TimeoutError,
        ):
            return False

    inst = redis.Redis(
        host=docker_ip,
        port=docker_services.port_for("redis", 6379),
    )
    docker_services.wait_until_responsive(
        timeout=30.0, pause=0.1, check=lambda: is_responsive(inst)
    )
    return inst


@pytest.fixture
def request_headers() -> dict:
    return {"Content-Type": "application/json"}
