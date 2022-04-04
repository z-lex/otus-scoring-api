install:
	python -m pip install -U pip setuptools
	python -m pip install .

install-dev:
	python -m pip install -U pip setuptools
	python -m pip install -e .[linters,formatters]

format:
	autoflake src/
	isort .
	black .

check:
	flake8 .

test:
	python -m unittest tests.py