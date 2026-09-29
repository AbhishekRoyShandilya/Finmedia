@echo off
REM Finmedia Research Desk: builds the web app on first run, then starts the server on http://127.0.0.1:8020
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Creating the Python environment...
  python -m venv .venv || goto :fail
  ".venv\Scripts\python.exe" -m pip install -e ".[dev]" || goto :fail
)
if not exist "web\dist\index.html" (
  echo Building the web app ^(needs Node.js^)...
  pushd web
  call npm install --no-audit --no-fund || goto :failpop
  call npm run build || goto :failpop
  popd
)
if not exist ".env" echo NOTE: no .env file yet - copy .env.example to .env and add your keys. Running in the mode set in config\settings.yaml.
start "" http://127.0.0.1:8020
".venv\Scripts\finmedia.exe" serve %*
goto :eof
:failpop
popd
:fail
echo Setup failed - see the messages above.
pause
