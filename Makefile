# settings

PY := python3
ENV_NAME := .venv

# computed

ACTIV_ENV := . $(ENV_NAME)/bin/activate
IN_ENV := $(ACTIV_ENV) &&

# includes
-include *.mk

# actions

help:
	$(PY) main.py -h

activate:
	# warning: will not work (limitation of `make`), you need to run it manually
	. $(ENV_NAME)/bin/activate

py_init:
	@echo "\n[[ creating python environment if absent ]]"
	$(PY) -m venv $(ENV_NAME)

py_dep: py_init
	@echo "\n[[ installing/upgrading python dependencies ]]"
	$(IN_ENV) python3 -m pip install --upgrade pip
	$(IN_ENV) pip install --upgrade -r requirements.txt

local_dep:
	@echo "\n[[ generating local files ]]"
	mkdir -p input/ver/ && cp -r input/ver.bak/* input/ver/

setup: py_init py_dep local_dep

rm_cache:
	@echo "\n[[ removing all pycache folders ]]"
	find . -name __pycache__ -prune -print -exec rm -rf {} \;

rm_temp:
	@echo "\n[[ removing generated temporary files ]]"
	rm -f yosys_graph.log

rm_pyenv:
	@echo "\n[[ removing the virtual python environment ]]"
	rm -rf $(ENV_NAME)

clean: rm_pyenv rm_cache rm_temp
