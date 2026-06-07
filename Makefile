.PHONY: setup test run check-db seed

setup:
	python -m venv .venv
	.venv/bin/pip install -r requirements.txt

test:
	.venv/bin/python -m pytest -q

run:
	.venv/bin/python cli.py

check-db:
	.venv/bin/python -c "from db import get_connection; get_connection().__enter__(); print('DB OK')"

seed:
	.venv/bin/python seed.py --reset
