@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

:: Настройки
set ENV_NAME=my_project_env
set PYTHON_VERSION=3.12
set CONDA_PATH=E:\Anaconda3
set REQUIREMENTS_FILE=requirements.txt
set SMOKE_TEST_SCRIPT=broken_env.py

echo ==============================================
echo Запуск setup_env.bat для проекта
echo ==============================================

:: Шаг 1: Проверяем, существует ли conda.bat по указанному пути
echo [1] Проверка наличия conda...
if not exist "%CONDA_PATH%\Scripts\conda.exe" (
    echo [ERROR] Не удалось найти conda по пути: %CONDA_PATH%
    echo Пожалуйста, проверьте правильность пути в файле setup_env.bat
    exit /b 1
)
echo [ok] Conda найдена.

:: Шаг 2: Проверяем, существует ли уже окружение с таким именем
echo [2] Проверка окружения %ENV_NAME%...
call "%CONDA_PATH%\Scripts\conda.exe" env list | findstr /b "%ENV_NAME%" >nul
if !errorlevel! equ 0 (
    echo [ok] Окружение %ENV_NAME% уже существует.
) else (
    echo Окружение не найдено. Создаю новое окружение %ENV_NAME% с Python %PYTHON_VERSION%...
    call "%CONDA_PATH%\Scripts\conda.exe" create -n %ENV_NAME% python=%PYTHON_VERSION% -y
    if !errorlevel! neq 0 (
        echo [ERROR] Не удалось создать окружение.
        exit /b 1
    )
    echo [ok] Окружение создано.
)

:: Шаг 3: Установка зависимостей из requirements.txt
echo [3] Установка зависимостей из %REQUIREMENTS_FILE%...
if not exist "%REQUIREMENTS_FILE%" (
    echo [ERROR] Файл %REQUIREMENTS_FILE% не найден в корне проекта!
    exit /b 1
)

echo Устанавливаю pandas через conda run...
call "%CONDA_PATH%\Scripts\conda.exe" run -n %ENV_NAME% python -m pip install -r %REQUIREMENTS_FILE%
if !errorlevel! neq 0 (
    echo [ERROR] Не удалось установить зависимости.
    exit /b 1
)
echo [ok] Зависимости установлены.

:: Шаг 4: Smoke test (проверка)
echo [4] Запуск smoke test (%SMOKE_TEST_SCRIPT%)...
call "%CONDA_PATH%\Scripts\conda.exe" run -n %ENV_NAME% python %SMOKE_TEST_SCRIPT%
if !errorlevel! equ 0 (
    echo ==============================================
    echo [ok] Скрипт выполнен успешно. Всё готово!
    echo ==============================================
    exit /b 0
) else (
    echo ==============================================
    echo [ERROR] Smoke test провален. Что-то пошло не так.
    echo ==============================================
    exit /b 1
)

ENDLOCAL