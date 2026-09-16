@echo off
setlocal
cd /d "%~dp0"

echo ================================================
echo   Ranking Marketing - Compilacion para Windows
echo ================================================
echo.

where py >nul 2>nul
if %errorlevel%==0 (
    set PYTHON_CMD=py
) else (
    where python >nul 2>nul
    if errorlevel 1 (
        echo ERROR: Python no esta instalado o no esta en PATH.
        echo Instala Python 3.11, 3.12 o 3.13 desde python.org y vuelve a ejecutar este archivo.
        pause
        exit /b 1
    )
    set PYTHON_CMD=python
)

if not exist ".venv-build\Scripts\python.exe" (
    echo [1/4] Creando entorno de compilacion...
    %PYTHON_CMD% -m venv .venv-build
    if errorlevel 1 goto :error
) else (
    echo [1/4] Entorno de compilacion existente.
)

set VPY=.venv-build\Scripts\python.exe

echo [2/4] Instalando dependencias...
"%VPY%" -m pip install --upgrade pip
if errorlevel 1 goto :error
"%VPY%" -m pip install -r requirements-build.txt
if errorlevel 1 goto :error

echo [3/4] Ejecutando pruebas...
"%VPY%" -m pytest -q
if errorlevel 1 goto :error

echo [4/4] Generando RankingMarketing.exe...
"%VPY%" -m PyInstaller --noconfirm --clean RankingMarketing.spec
if errorlevel 1 goto :error

echo.
echo ================================================
echo LISTO
echo Ejecutable: %CD%\dist\RankingMarketing.exe
echo ================================================
explorer "%CD%\dist"
pause
exit /b 0

:error
echo.
echo ERROR: La compilacion se detuvo. Revisa el mensaje anterior.
pause
exit /b 1
