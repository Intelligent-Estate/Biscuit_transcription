@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%" >nul

set "PYTHONPATH=%SCRIPT_DIR%src"
where pythonw.exe >nul 2>nul
if "%ERRORLEVEL%"=="0" (
    start "" /b pythonw.exe -m biscuit %*
) else (
    start "" /min python.exe -m biscuit %*
)

popd >nul
exit /b 0
