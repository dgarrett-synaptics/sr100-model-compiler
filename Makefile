.PHONY: lint check_format format tests check all

all: check_format tests

lint:
	pylint src/srmodel

check_format:
	black --check src/srmodel tests

format:
	black src/srmodel tests

tests:
	pytest tests
