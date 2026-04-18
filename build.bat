@echo off
:: ============================================================
::  build.bat  –  compile dff_to_glb.py into a standalone EXE
:: ============================================================
::
::  The EXE still requires:
::    • Blender installed (path set in converter.cfg)
::    • DragonFF-master folder (path set in converter.cfg)
::    • blender_worker.py  next to the EXE
::
::  blender_worker.py is NOT bundled inside the EXE — it must
::  sit in the same folder as dff_to_glb.exe at runtime.
:: ============================================================

echo.
echo  [1/3] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Python not found. Install from https://python.org
    pause & exit /b 1
)

echo  [2/3] Installing PyInstaller...
python -m pip install --upgrade pip >nul
python -m pip install pyinstaller
if errorlevel 1 (
    echo  ERROR: pip install failed.
    pause & exit /b 1
)

echo  [3/3] Building EXE...
pyinstaller ^
    --onefile ^
    --console ^
    --name dff_to_glb ^
    --clean ^
    dff_to_glb.py

if errorlevel 1 (
    echo.
    echo  ERROR: PyInstaller build failed.
    pause & exit /b 1
)

:: Copy blender_worker.py next to the EXE (it must travel with it)
copy /Y blender_worker.py dist\blender_worker.py >nul
copy /Y converter.cfg     dist\converter.cfg     >nul

echo.
echo  ============================================================
echo   BUILD COMPLETE
echo   dist\
echo     dff_to_glb.exe       <- launcher
echo     blender_worker.py    <- Blender worker  (keep next to exe)
echo     converter.cfg        <- edit paths here
echo  ============================================================
echo.
echo  Edit dist\converter.cfg, then run dist\dff_to_glb.exe
echo.
pause
