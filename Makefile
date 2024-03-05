# settings

PY := python3
ENV_NAME := venv

SFTW_DEP := graphviz graphviz-dev yosys opensta

# This will not be needed as the main.py already creates the folders
EXTRA_FOLDERS := test/ver test/z3
EXTRA_FOLDERS += output/aig output/area output/delay output/figure output/gv output/json output/log output/report output/ver output/z3

# computed

ACTIV_ENV := . $(ENV_NAME)/bin/activate
IN_ENV := $(ACTIV_ENV) &&

# includes
-include *.mk

# actions

run:
	$(PY) main.py -h

activate:
	# warning: will not work (limitation of `make`), you need to run it manually
	. venv/bin/activate

py_init:
	@echo "\n[[ creating python environment if absent ]]"
	$(PY) -m venv $(ENV_NAME)

py_dep: py_init
	@echo "\n[[ installing/upgrading python dependencies ]]"
	$(IN_ENV) python3 -m pip install --upgrade pip
	$(IN_ENV) pip install --upgrade -r requirements.txt

sftw_dep:
	@echo "\n[[ installing/upgrading software dependencies ]]"
	sudo apt install --yes --upgrade $(SFTW_DEP)

folders_dep:
	@echo "\n[[ creating required folders ]]"
	$(if $(strip $(EXTRA_FOLDERS)),mkdir -p $(EXTRA_FOLDERS),# nothing to create)

local_dep:
	@echo "\n[[ generating local files ]]"
	mkdir -p input/ver/ && cp -r input/ver.bak/* input/ver/
	touch -a local.mk

setup: folders_dep py_init py_dep local_dep
setup-all: sftw_dep setup

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
