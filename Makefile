all: help

sync:
	@uv sync -q

init: sync
	@echo "Run:  . .venv/bin/activate"

clean:
	rm -rf uv.lock
	rm -rf .venv
	rm -rf dist
	rm -rf build
	rm -rf *.spec
	rm -rf .coverage
	rm -rf */*.pyc */__pycache__ .pytest_cache */*.egg-info
	rm -rf *.pyz *.zip
	rm -rf output

.PHONY: test
test: sync
	@echo "Running unittests"
	@uv run python -B -m unittest discover -v

pytest: sync
	@echo "Running pytest"
	@uv run pytest

pylint: sync
	@echo "Running pylint"
	@uv run pylint --include-naming-hint=y **/*.py

style: sync
	@uv run pycodestyle . --verbose --exclude=.git,.venv,output && echo "Style is OK"

coverage: sync
	@uv run coverage run --source=./src -m unittest discover -v
	@uv run coverage report -m

sanity: sync
	@uv run bash test/sanity.sh

build: sync
	@mkdir -p build/fake && touch build/fake/hook-jira.py
	@uv run pyinstaller --clean --onefile --additional-hooks-dir=build/fake --name=gojira src/__main__.py

help:
	@echo "Note: UV package manager for python is required"
	@echo "      https://github.com/astral-sh/uv"
	@echo "Goals:"
	@echo "   make init      - fetch all dependencies to .venv"
	@echo "   make clean     - remove test and python artifacts"
	@echo "   make style     - run pycodestyle"
	@echo "   make pylint    - run pylint"
	@echo "   make test      - run unit tests"
	@echo "   make pytest    - run pytest"
#	@echo "   make coverage  - run coverage tool"
#	@echo "   make sanity    - run all tests and common scenarios"
	@echo "   make build     - create executable binary"
	@echo
