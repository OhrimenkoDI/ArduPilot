@echo off
setlocal

set "ROOT=%~dp0"
set "PYTHON=%ROOT%venv\Scripts\python.exe"
set "SCRIPT=%ROOT%listen_14551.py"

if not exist "%PYTHON%" (
    echo [ERROR] Python not found: "%PYTHON%"
    pause
    exit /b 1
)

if not exist "%SCRIPT%" (
    echo [ERROR] Script not found: "%SCRIPT%"
    pause
    exit /b 1
)

pushd "%ROOT%"
"%PYTHON%" "%SCRIPT%"
set "EXITCODE=%ERRORLEVEL%"
popd

echo.
echo Listener exited with code %EXITCODE%.
pause
exit /b %EXITCODE%
