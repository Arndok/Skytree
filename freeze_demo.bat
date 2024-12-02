set PYTHONPATH=%cd%\src
set PYTHON_EXE=C:\Users\harol\AppData\Local\Microsoft\WindowsApps\python3.11.exe
%PYTHON_EXE% -m cx_Freeze src\skytree\examples.py --target-dir demo --target-name skytree_demo.exe --icon src\skytree\example_resources\icon.ico
pause