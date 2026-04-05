@echo off
title GLaDOS Chat - First Time Setup
echo ============================================================
echo   GLaDOS Voice Chat - First Time Setup
echo ============================================================
echo.

cd /d "%~dp0"

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install Python 3.10+ and add to PATH.
    pause
    exit /b 1
)

:: Create venv if it doesn't exist
echo [1/3] Setting up virtual environment...
if not exist "venv" (
    python -m venv venv
)
call venv\Scripts\activate.bat
echo       Done.

:: Install Python dependencies (torch + transformers can be large)
echo [2/3] Installing Python dependencies (this may take a while first time)...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)
echo       Done.

:: Download GLaDOS TTS models if missing
echo [3/3] Checking GLaDOS TTS models...
if not exist "GLaDOS-TTS\glados\models\glados.onnx" (
    echo       Downloading glados.onnx...
    curl -L "https://github.com/dnhkng/GlaDOS/releases/download/0.1/glados.onnx" -o "GLaDOS-TTS\glados\models\glados.onnx"
)
if not exist "GLaDOS-TTS\glados\models\phomenizer_en.onnx" (
    echo       Downloading phomenizer_en.onnx...
    curl -L "https://github.com/dnhkng/GlaDOS/releases/download/0.1/phomenizer_en.onnx" -o "GLaDOS-TTS\glados\models\phomenizer_en.onnx"
)
echo       Done.

echo.
echo   NOTE: The Gemma 4 E2B model will be downloaded from HuggingFace
echo   automatically on first launch (~4-5GB).
echo.
echo ============================================================
echo   Setup complete! Run "run.bat" to start GLaDOS Chat.
echo ============================================================
pause
