@echo off
REM KiNotes Plugin Update Script
REM Copies latest development files to KiCad plugins directory
REM Run this after making changes to sync with KiCad

setlocal
set "DEV_DIR=D:\AI_tools\PCBtools\KiNotes\KiNotes\KiNotes"
set "PLUGIN_DIR=C:\Users\prami\OneDrive\Documents\KiCad\9.0\scripting\plugins\KiNotes"

echo ========================================
echo KiNotes Plugin Update
echo ========================================
echo.

REM Check if directories exist
if not exist "%DEV_DIR%" (
    echo ERROR: Development directory not found: %DEV_DIR%
    pause
    exit /b 1
)

if not exist "%PLUGIN_DIR%" (
    echo ERROR: KiCad plugin directory not found: %PLUGIN_DIR%
    pause
    exit /b 1
)

echo Copying files from development to KiCad...
echo.

REM Copy root files
echo [1/5] Copying root files...
xcopy /Y "%DEV_DIR%\__init__.py" "%PLUGIN_DIR%\" > nul
xcopy /Y "%DEV_DIR%\kinotes_action.py" "%PLUGIN_DIR%\" > nul

REM Copy core modules
echo [2/5] Copying core modules...
xcopy /Y /E "%DEV_DIR%\core\*.py" "%PLUGIN_DIR%\core\" > nul

REM Copy UI modules
echo [3/5] Copying UI modules...
xcopy /Y /E "%DEV_DIR%\ui\*.py" "%PLUGIN_DIR%\ui\" > nul
xcopy /Y /E "%DEV_DIR%\ui\components\*.py" "%PLUGIN_DIR%\ui\components\" > nul
xcopy /Y /E "%DEV_DIR%\ui\dialogs\*.py" "%PLUGIN_DIR%\ui\dialogs\" > nul
xcopy /Y /E "%DEV_DIR%\ui\tabs\*.py" "%PLUGIN_DIR%\ui\tabs\" > nul

REM Copy resources
echo [4/5] Copying resources...
xcopy /Y /E "%DEV_DIR%\resources\*" "%PLUGIN_DIR%\resources\" > nul

REM Clear Python cache
echo [5/5] Clearing Python cache...
if exist "%PLUGIN_DIR%\__pycache__\" rmdir /S /Q "%PLUGIN_DIR%\__pycache__" 2>nul
if exist "%PLUGIN_DIR%\core\__pycache__\" rmdir /S /Q "%PLUGIN_DIR%\core\__pycache__" 2>nul
if exist "%PLUGIN_DIR%\ui\__pycache__\" rmdir /S /Q "%PLUGIN_DIR%\ui\__pycache__" 2>nul
if exist "%PLUGIN_DIR%\ui\components\__pycache__\" rmdir /S /Q "%PLUGIN_DIR%\ui\components\__pycache__" 2>nul
if exist "%PLUGIN_DIR%\ui\dialogs\__pycache__\" rmdir /S /Q "%PLUGIN_DIR%\ui\dialogs\__pycache__" 2>nul
if exist "%PLUGIN_DIR%\ui\tabs\__pycache__\" rmdir /S /Q "%PLUGIN_DIR%\ui\tabs\__pycache__" 2>nul

echo.
echo ========================================
echo UPDATE COMPLETE!
echo ========================================
echo.
echo Next steps:
echo 1. Close KiCad completely
echo 2. Restart KiCad
echo 3. Open a PCB file
echo 4. Check Tools ^> External Plugins ^> KiNotes
echo.
echo Plugin location: %PLUGIN_DIR%
echo.
pause
