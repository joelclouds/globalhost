VENV := venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
TWINE := $(VENV)/bin/twine

.PHONY: venv install build publish clean distclean example-django example-fastapi example-flask example-streamlit

venv:
	python3 -m venv $(VENV)
	$(PIP) install -r requirements.txt

install: venv
	$(PIP) install -e .

build: venv
	$(PYTHON) -m build

publish: build
	$(TWINE) upload dist/*

example-django: install
	$(PYTHON) examples/django/01_json_api.py

example-fastapi: install
	$(PYTHON) examples/fastapi/01_json_api.py

example-flask: install
	$(PYTHON) examples/flask/01_json_api.py

example-streamlit: install
	$(PYTHON) examples/streamlit/01_json_api.py

# Removes build artifacts, caches, and egg-info
clean:
	find . -type d \( -name "__pycache__" -o -name "dist" -o -name "build" -o -name "*.egg-info" \) -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf src/globalhost/bin

# Nukes the virtual environment too (returns repo to a freshly cloned state)
distclean: clean
	rm -rf $(VENV)
