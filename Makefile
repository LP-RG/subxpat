# settings

PY := python3
VENV := venv

# computed

BIN := $(VENV)/bin
IN_ENV := . $(BIN)/activate &&

# actions

run:
	$(PY) main.py -h

activate:
	. venv/bin/activate # doesn't work

setup:
	$(PY) -m venv $(VENV)
	$(IN_ENV) $(BIN)/python3 -m pip install --upgrade pip
	$(IN_ENV) $(BIN)/pip install --upgrade -r requirements.txt

clean:
	rm -rf __pycache__
	rm -rf $(VENV)
