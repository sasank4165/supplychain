@echo off
REM Tag Validation Script for Windows
REM Usage: validate-tags.bat [environment] [--strict]

setlocal

set ENVIRONMENT=%1
set STRICT=%2

if "%ENVIRONMENT%"=="" (
    echo Usage: validate-tags.bat [dev^|staging^|prod] [--strict]
    exit /b 1
)

echo Validating tags for environment: %ENVIRONMENT%
echo.

python scripts\validate-tags.py --environment %ENVIRONMENT% %STRICT%

if %ERRORLEVEL% neq 0 (
    echo.
    echo Tag validation failed!
    exit /b 1
)

echo.
echo Tag validation passed!
exit /b 0
