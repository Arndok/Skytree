@echo off
set PYTHON_EXE=python3.11
set PYTHONPATH=%cd%\src
%PYTHON_EXE% -m skytree.examples
pause