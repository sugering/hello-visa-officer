@echo off
rem Hello Visa Officer - demo launcher (Windows).
rem Needs Python 3.10+ with Pillow. Tries the py launcher first, then python on PATH.
setlocal
set "PY=py -3"
where py >nul 2>nul || set "PY=python"
%PY% "%~dp0demo\app.py" %*
if errorlevel 1 pause
