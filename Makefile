.PHONY: lint check_format format test check all

lint:
	pylint src/srmodel

check_format:
	black --check src/srmodel tests

format:
	black src/srmodel tests

test:
	pytest tests

check: lint check_format test

all:
	black src/srmodel tests
	pylint src/srmodel
	pytest tests

