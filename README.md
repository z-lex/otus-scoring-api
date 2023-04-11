# Otus Scoring API

## Dependencies

* redis
* Python >= 3.7
* redis-py

### Optional development dependencies

* docker
* pytest
* pytest-docker
* requests
* flake8
* flake8-pyproject
* black
* isort
* autoflake

## Installation

```shell
$ python3 -m pip install "otus-scoring-api @ git+https://github.com/z-lex/otus-scoring-api@master"
```

## Usage

```shell
$ otus-scoring-api-server [-p <port>] [-l <logfile>] [-r <redis-url>]
```

## Development

Clone the repository and run this in a project's virtual environment:

```shell
$ make install-dev
```

To format code:

```shell
$ make format
```

To run linters:

```shell
$ make check
```

To run unit tests:

```shell
$ make test-unit
```

To run integration tests (requires docker installed):

```shell
$ make test-integration
```

To run all tests:

```shell
$ make test
```

