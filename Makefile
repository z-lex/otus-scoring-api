install:
	python -m pip install -U pip setuptools
	python -m pip install .

install-dev:
	python -m pip install -U pip setuptools
	python -m pip install -e .[linters,formatters,testing]

format:
	autoflake src/
	isort .
	black .

check:
	flake8 .

test-unit:
	pytest tests/unit

test-integration:
	pytest --rootdir=tests/integration tests/integration

test: test-unit test-integration