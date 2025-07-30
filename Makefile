.PHONY: lint check_format format test check all

all: check_format test

lint:
	pylint src/sr100_model_compiler/sr100_model_compiler.py
	pylint tests
	#pylint src/sr100_model_compiler

check_format:
	black --check src/sr100_model_compiler tests

format:
	black --line-length 88 src/sr100_model_compiler tests

test:
	pytest tests
