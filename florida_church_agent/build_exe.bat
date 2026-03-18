@echo off
setlocal

python -m venv .venv
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pyinstaller --clean church_agent.spec

echo Build complete. Executable located in dist\florida_church_agent\
endlocal
