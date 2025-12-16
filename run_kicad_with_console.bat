@echo off
REM Run KiCad with console output visible
REM This allows us to see [KiNotes] debug messages

echo ========================================
echo KiCad Console Output Capture
echo ========================================
echo.
echo This will open KiCad with console visible.
echo All [KiNotes] debug messages will appear here.
echo.
echo Steps to test:
echo 1. KiCad window opens
echo 2. Open a PCB file
echo 3. Click Tools ^> External Plugins ^> KiNotes
echo 4. Use plugin briefly
echo 5. Close plugin (X button)
echo 6. Watch THIS console for cleanup messages
echo 7. Repeat step 3-5 five times
echo 8. Copy console output when done
echo.
echo ========================================
echo.

REM Find KiCad executable
set KICAD_EXE=C:\Program Files\KiCad\9.0\bin\kicad.exe

if not exist "%KICAD_EXE%" (
    echo ERROR: KiCad not found at %KICAD_EXE%
    echo Please verify KiCad 9.0 installation path
    pause
    exit /b 1
)

echo Starting KiCad from: %KICAD_EXE%
echo.
echo [Console output will appear below]
echo ========================================
echo.

REM Run KiCad with console visible
"%KICAD_EXE%"

echo.
echo ========================================
echo KiCad closed
echo ========================================
pause
