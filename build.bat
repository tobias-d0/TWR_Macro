@echo off

if exist build rmdir /S /Q build
if exist dist rmdir /S /Q dist

pyinstaller --clean --onefile --name TWR_Macro main.py

xcopy "data" "dist\data" /E /I /Y

echo.
echo Build complete.
pause