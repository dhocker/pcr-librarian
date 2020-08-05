#!/bin/zsh

# Build macOS X version of pcr_librarian app

source `which virtualenvwrapper.sh`
workon pcr800
python setup.py py2app
deactivate
