# settings

PY := python3
ENV_NAME := venv

SFTW_DEP := graphviz graphviz-dev yosys opensta

EXTRA_FOLDERS := 

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
	$(if $(strip $(EXTRA_FOLDERS)),mkdir -p $(EXTRA_FOLDERS),)

setup: sftw_dep folders_dep py_init py_dep

rm_cache:
	@echo "\n[[ removing all pycache folders ]]"
	find . -name __pycache__ -exec rm -r {} \;

rm_pyenv:
	@echo "\n[[ removing the virtual python environment ]]"
	rm -rf $(ENV_NAME)

clean: rm_cache rm_pyenv
