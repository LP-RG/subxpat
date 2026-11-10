# settings

PY := python3.14
ENV_NAME := .venv
DELETION_DELAY ?= 10

# computed

ACTIV_ENV := . $(ENV_NAME)/bin/activate
SETUP := ENV_NAME=$(ENV_NAME) PY=$(PY) bash setup/deps.sh

# includes
-include *.mk

# actions

help:
	$(PY) main.py -h

activate:
	# warning: will not work (limitation of `make`), you need to run it manually
	$(ACTIV_ENV)

py_init:
	@$(SETUP) --python-init

py_dep: py_init
	@$(SETUP) --python-dep

setup: py_init py_dep

macos: setup
	@$(SETUP) --macos

all: setup
	@$(SETUP) --all

rm_data:
	@echo "\n[[ deleting all final and intermediary data (output/) ]]\n[[ !! YOU HAVE $(DELETION_DELAY) SECONDS TO CANCEL THIS OPERATION !! ]]"
	@sleep $(DELETION_DELAY)
	rm -rf output/

rm_cache:
	@echo "\n[[ removing all pycache folders ]]"
	find . -name __pycache__ -prune -print -exec rm -rf {} \;

rm_temp:
	@echo "\n[[ removing generated temporary files ]]"
	rm -f .history_sta

rm_pyenv:
	@echo "\n[[ removing the virtual python environment ]]"
	rm -rf $(ENV_NAME)

rm_deps:
	@echo "\n[[ removing the locally built dependencies (.deps/) ]]\n[[ !! YOU HAVE $(DELETION_DELAY) SECONDS TO CANCEL THIS OPERATION !! ]]"
	@sleep $(DELETION_DELAY)
	rm -rf "$${DEPS_DIR:-.deps}"

clean: rm_cache rm_temp

clean-all: rm_pyenv rm_data rm_deps clean
