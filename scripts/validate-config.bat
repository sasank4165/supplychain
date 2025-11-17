@echo off
REM Configuration Validation Script for Windows
REM Validates configuration files before deployment

setlocal enabledelayedexpansion

set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..
set ENVIRONMENT=%1

if "%ENVIRONMENT%"=="" (
    echo Usage: validate-config.bat [environment]
    echo Example: validate-config.bat dev
    echo.
    echo Available environments: dev, staging, prod
    exit /b 1
)

echo ======================================================================
echo Validating configuration for environment: %ENVIRONMENT%
echo ======================================================================
echo.

REM Check if config file exists
if not exist "%PROJECT_ROOT%\config\%ENVIRONMENT%.yaml" (
    echo ERROR: Configuration file not found: config\%ENVIRONMENT%.yaml
    exit /b 1
)

echo [OK] Configuration file found: config\%ENVIRONMENT%.yaml

REM Try to run Python validation if available
where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo.
    echo Running Python validation script...
    py "%SCRIPT_DIR%validate-config.py" --environment %ENVIRONMENT%
    exit /b %ERRORLEVEL%
) else (
    where python >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo.
        echo Running Python validation script...
        python "%SCRIPT_DIR%validate-config.py" --environment %ENVIRONMENT%
        exit /b %ERRORLEVEL%
    ) else (
        echo.
        echo WARNING: Python not found. Skipping detailed validation.
        echo Please install Python to run full validation checks.
        echo.
        echo Basic validation passed.
        exit /b 0
    )
)
