.PHONY: lint check_format format test check all

all: check_format test

lint:
	pylint src/srmodel

check_format:
	black --check src/srmodel tests

format:
	black --line-length 88 src/srmodel tests

test:
	pytest tests
