@echo off
echo Building ThumbGen executable...
echo.

REM Install PyInstaller if not already installed
pip install pyinstaller

REM Navigate to web_ui directory
cd web_ui

REM Build using spec file
pyinstaller thumbgen_ui.spec --clean

echo.
echo Build complete!
echo Executable location: web_ui\dist\ThumbGen.exe
echo.
echo IMPORTANT: To distribute, copy these folders next to ThumbGen.exe:
echo   - Thumbnails folder (where users put their game assets)
echo   - output folder (where generated thumbnails go)
echo.
pause
