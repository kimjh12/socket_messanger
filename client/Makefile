PROJECT_NAME := $(shell python setup.py --name)

SHELL := /bin/bash
BOLD := \033[1m
DIM := \033[2m
RESET := \033[0m

.PHONY: all
all: uninstall install clean 

.PHONY: install
install:
	@echo -e "$(BOLD)installing $(PROJECT_NAME) $(RESET)"
	@echo -e -n "$(DIM)"
	@pip install .
	@echo -e -n "$(RESET)"

.PHONY: uninstall
uninstall:
	@echo -e "$(BOLD)uninstalling '$(PROJECT_NAME)'$(RESET)"
	-@pip uninstall -y $(PROJECT_NAME) 2> /dev/null

.PHONY: test
test: uninstall install
	@echo -e "$(BOLD)running test units for $(PROJECT_NAME) $(RESET)"
	@pythone -m unittest discover -s tests -p 'tests_*.py' --verbose
	@rm -rf tests/*.pyc

.PHONY: run
run: uninstall install
	@echo -e "$(BOLD)running"
	@python3 client.py

.PHONY: dist
dist:
	@echo -e -n "$(DIM)"
	@pyinstaller --onefile client.spec
	@echo -e -n "$(RESET)"

.PHONY: clean
clean:
	@echo -e "$(BOLD)cleaning $(PROJECT_NAME) $(RESET)"
	@rm -rf build $(PROJECT_NAME).egg-info
