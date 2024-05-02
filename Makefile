# Makefile to generate distribution packages.

.ONESHELL:
SHELL := bash

ifeq (${OSTYPE},cygwin)
 # on cygwin still use the windows native python to create distributions
 $(info Running on cygwin)
 # The python interpreter to use. Can be overriden from the environment:
 PYTHON?=python
else
 $(info Running not on cygwin)
 # The python interpreter to use. Can be overriden from the environment:
 PYTHON?=python3
endif

# \remark
#   'cp -a' yields a "preserving permissions for /cygdrive/m/Software/Python/Schunk/python-msp430-tools-0.6.win-amd64.exe: Not supported" error
#   but preseving the timestamps only works and is all we really want.
CP=cp -f --preserve=timestamps 

RELEASE_DIR=bkstools
PROJECT_RELEASE=${shell cd ${RELEASE_DIR} ; ${PYTHON} -c "import release ; print( release.PROJECT_RELEASE )"}
PROJECT_NAME=${shell cd ${RELEASE_DIR} ; ${PYTHON} -c "import release ; print( release.PROJECT_NAME )"}
PROJECT_DATE=${shell cd ${RELEASE_DIR} ; ${PYTHON} -c "import release ; print( release.PROJECT_DATE )"}


.PHONY: all
all: dist 

.PHONY: help
help:
	@echo "Makefile for ${PROJECT_NAME}"
	@echo "Targets:"
	@echo "  - all             - dist (without copy or upload)"
	@echo "  - dist            - generated all distribution packages + exe"
	@echo "  - bdist_wheel     - generate a binary wheel package"
	# bdist_wininst is deprecated! 	@echo "  - bdist_wininst   - generate a binary windows installer package"
	# bdist_wininst is deprecated! 	@echo "  - bdist_wininst64 - generate a binary windows installer package for 64-bit"
	@echo "  - sdist_bztar     - generate a source distribution in tar.bz2 format"
	@echo "  - exe             - generate standalone executable with py2exe"
	@echo "                      - uncompressed in build/${PROJECT_NAME}-${PROJECT_RELEASE}-py2exe/"
	@echo "                      - zipped in dist/${PROJECT_NAME}-${PROJECT_RELEASE}-py2exe.zip"
	@echo "  - clean           - clean up current build in ./build/"
	@echo "  - mrproper        - clean + clean up current distributions in ./dist/"
	@echo "  - show            - show some variables used/derived by the makefile"
	@echo "  - venv            - setup the python virtualenv environment required for building the frozen exes"
	@echo "  - venv-clean      - remove the python virtualenv environment venv"
	@echo "  - venv-pip-list   - do a pip list in the virtualenv environment venv"
	

.PHONY: show
show:
	@echo "PYTHON=${PYTHON}"
	@echo "PROJECT_RELEASE=${PROJECT_RELEASE}"
	@echo "PROJECT_NAME=${PROJECT_NAME}"
	@echo "PROJECT_DATE=${PROJECT_DATE}"

.PHONY: dist
dist: bdist_wheel sdist_bztar exe
# bdist_wininst bdist_wininst64  # bdist_wininst is deprecated! 
	
.PHONY: clean
clean:
	rm -rf build/*

.PHONY: mrproper
mrproper: clean venv-clean
	rm -rf dist/${PROJECT_NAME}-${PROJECT_RELEASE}*

#---

.PHONY: bdist_wheel
bdist_wheel: 
	if [ -e "./venv/Scripts/activate" ]; then
	    # running on cygwin/windows
	    activate="./venv/Scripts/activate"
	else
	    # running on Linux
	    activate="./venv/bin/activate"
	fi  
	source "$${activate}"
	${PYTHON} setup.py $@

.PHONY: bdist_wininst
bdist_wininst: 
	source ./venv/Scripts/activate	
	${PYTHON} setup.py bdist_wininst
	chmod a+x dist/*.exe

.PHONY: bdist_wininst64
bdist_wininst64:
	source ./venv/Scripts/activate	
	${PYTHON} setup.py bdist_wininst --plat-name=win-amd64
	chmod a+x dist/*.exe
	
.PHONY: sdist_bztar
sdist_bztar:
	${PYTHON} setup.py sdist --formats bztar          

#---

	
		
.PHONY: exe
exe:  
	mkdir -p dist ; \
	source ./venv/Scripts/activate	
	${PYTHON} setup.py py2exe
	pip freeze > build/${PROJECT_NAME}-${PROJECT_RELEASE}-py2exe/requirements.txt	
	
	cd build && zip -r -o ../dist/${PROJECT_NAME}-${PROJECT_RELEASE}-py2exe.zip ${PROJECT_NAME}-${PROJECT_RELEASE}-py2exe/	

	#---

.PHONY: venv
venv:
	set -e
	#virtualenv venv # does not work. (Generating exes with py2exe yields "ImportError: No module named pkg_resources._vendor.pyparsing"
	${PYTHON} -m venv venv
	if [ -e "./venv/Scripts/activate" ]; then
	    # running on cygwin/windows
	    activate="./venv/Scripts/activate"
	    dos2unix $${activate}
	    extra_packages="pypiwin32 py2exe pydevd"
	else
	    # running on Linux
	    activate="./venv/bin/activate"
	    extra_msg="For the GUI tools 'bks_status' and 'bks_jog' you might have to install tkinter\nand idle3 packages. These are not available via pip, so use something like\n> sudo apt-get install python3-tk\nand\n> sudo apt-get install idle3"
	fi  
	source "$${activate}"
	pip install requests pyyaml minimalmodbus wrapt $${extra_packages}  # for running 
	pip install chardet wheel                                           # for building exes and wheels
	
	# pip install --upgrade setuptools
	pip list
	@echo -e "\nTip: To activate the python virtual environment venv in your shell use \" source $${activate} \"\n$${extra_msg}"
	######################################
	# Command output starts below

.PHONY: venv-clean
venv-clean:
	rm -rf venv/
	
.PHONY: venv-pip-list
venv-pip-list:
	source ./venv/Scripts/activate
	pip list
	
.PHONY: exes-run
exes-run:
	for exe in build/${PROJECT_NAME}-${PROJECT_RELEASE}-int-py2exe/*.exe ; do
	  echo "==="
	  echo "$${exe} -h:"
	  $${exe} -h
	  echo
	done
	