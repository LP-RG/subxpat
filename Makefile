PY = python3
VENV = venv
BIN=$(VENV)/bin
run:
	$(PY) main.py -h
activate:
	. venv/bin/activate # doesn't work
requirements:
	python3 -m pip install --upgrade pip
	$(BIN)/pip install --upgrade -r requirements.txt
setup:
	$(PY) -m venv $(VENV)

clean:
	rm -rf __pycache__
	rm -rf $(VENV)
