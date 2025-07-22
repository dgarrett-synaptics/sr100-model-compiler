.PHONY: lint format test check all

lint:
	pylint src/srmodel

format:
	black --check src/srmodel tests

test:
	pytest tests

check: lint format test

all:
	black src/srmodel tests
	pylint src/srmodel
	pytest tests

