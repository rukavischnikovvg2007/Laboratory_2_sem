@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

:: Переходим в папку, где лежит сам скрипт
cd /d "%~dp0"

:: Поднимаемся на уровень выше (в корень проекта)
cd ..

:: Settings
set ENV_NAME=Laboratory_2_sem
set PYTHON_VERSION=3.12
set REQUIREMENTS_FILE=requirements.txt
set SMOKE_TEST_SCRIPT=broken_env.py

echo ==============================================
echo Starting setup_env.bat for project
echo ==============================================
echo.

:: Step 1: Automatic conda search
echo [1] Searching for conda...

set CONDA_FOUND=0
set CONDA_PATHS=^
%USERPROFILE%\anaconda3 ^
%USERPROFILE%\Anaconda3 ^
C:\ProgramData\Anaconda3 ^
C:\Program Files\Anaconda3 ^
C:\Anaconda3 ^
D:\Anaconda3 ^
E:\Anaconda3

for %%p in (%CONDA_PATHS%) do (
    if exist "%%p\Scripts\conda.exe" (
        set CONDA_PATH=%%p
        set CONDA_FOUND=1
        echo [ok] Conda found at: %%p
        goto :conda_found
    )
)

:conda_found
if !CONDA_FOUND! equ 0 (
    echo [ERROR] Conda not found. Please install Anaconda or Miniconda.
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

:: Step 2: Check if environment already exists
echo.
echo [2] Checking environment %ENV_NAME%...
call "!CONDA_PATH!\Scripts\conda.exe" env list | findstr /b "%ENV_NAME%" >nul
if !errorlevel! equ 0 (
    echo [ok] Environment %ENV_NAME% already exists.
) else (
    echo Environment not found. Creating new environment %ENV_NAME% with Python %PYTHON_VERSION%...
    call "!CONDA_PATH!\Scripts\conda.exe" create -n %ENV_NAME% python=%PYTHON_VERSION% -y
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to create environment.
        echo.
        echo Press any key to exit...
        pause >nul
        exit /b 1
    )
    echo [ok] Environment created.
)

:: Step 3: Install dependencies from requirements.txt
echo.
echo [3] Installing dependencies from %REQUIREMENTS_FILE%...
if not exist "%REQUIREMENTS_FILE%" (
    echo [ERROR] File %REQUIREMENTS_FILE% not found in project root!
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

echo Installing pandas via conda run...
call "!CONDA_PATH!\Scripts\conda.exe" run -n %ENV_NAME% python -m pip install -r %REQUIREMENTS_FILE%
if !errorlevel! neq 0 (
    echo [ERROR] Failed to install dependencies.
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b 1
)
echo [ok] Dependencies installed.

:: Step 4: Smoke test
echo.
echo [4] Running smoke test (%SMOKE_TEST_SCRIPT%)...
call "!CONDA_PATH!\Scripts\conda.exe" run -n %ENV_NAME% python %SMOKE_TEST_SCRIPT%
if !errorlevel! equ 0 (
    echo.
    echo ==============================================
    echo [ok] Script completed successfully. All ready!
    echo ==============================================
) else (
    echo.
    echo ==============================================
    echo [ERROR] Smoke test failed. Something went wrong.
    echo ==============================================
)

:: Wait for user to press any key before closing
echo.
echo Press any key to exit...
pause >nul
ENDLOCAL
