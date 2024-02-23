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

input_dep:
	@echo "\n[[ copying inputs in input/ver/ ]]"
	mkdir -p input/ver/
	cp -r input/ver.bak/* input/ver/
	
setup: folders_dep py_init py_dep input_dep
setup-all: sftw_dep folders_dep py_init py_dep

rm_cache:
	@echo "\n[[ removing all pycache folders ]]"
	find . -name __pycache__ -prune -print -exec rm -rf {} \;

rm_pyenv:
	@echo "\n[[ removing the virtual python environment ]]"
	rm -rf $(ENV_NAME)

clean: rm_cache rm_pyenv

REQUIRED_OBJECTS := config input sxpat z_marco
REQUIRED_OBJECTS += Makefile requirements.txt
REQUIRED_OBJECTS += v2_testing.py temp_main6.py
send_package:
	scp -r $(REQUIRED_OBJECTS) $(user)@10.21.12.72:$(directory)

files ?= Documents/11_jan/11_jan.log Documents/11_jan/11_jan.2.log Documents/18_jan/18_jan.log Documents/18_jan2/18_jan2.log
gather_logs:
	mkdir -p from_remote
	scp -T $(user)@10.21.12.72:"$(files)" from_remote/
