# Otus Scoring API

## Dependencies

* Python >= 3.7

### Optional development dependencies

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
$ otus-scoring-api-server [-p <port>] [-l <logfile>]
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

To run tests:

```shell
$ make test
```

