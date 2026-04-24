@echo off
setlocal

set "ROOT=%~dp0"
set "PYTHON=%ROOT%venv\Scripts\python.exe"
set "MAVPROXY=%ROOT%venv\Scripts\mavproxy.py"

if not exist "%PYTHON%" (
    echo [ERROR] Python not found: "%PYTHON%"
    pause
    exit /b 1
)

if not exist "%MAVPROXY%" (
    echo [ERROR] MAVProxy script not found: "%MAVPROXY%"
    pause
    exit /b 1
)

pushd "%ROOT%"

echo Starting MAVProxy...
echo Python: "%PYTHON%"
echo Script: "%MAVPROXY%"
echo.

"%PYTHON%" "%MAVPROXY%" ^
    --master=udp:0.0.0.0:14550 ^
    --out=udp:127.0.0.1:14551 ^
    --out=udpin:0.0.0.0:14553

set "EXITCODE=%ERRORLEVEL%"
popd

echo.
echo MAVProxy exited with code %EXITCODE%.
pause
exit /b %EXITCODE%
