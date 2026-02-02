@echo off
echo ==========================================
echo Instalando dependencias do projeto...
echo ==========================================
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo [ERRO] Houve um problema na instalacao.
    pause
    exit /b %errorlevel%
)

echo.
echo ==========================================
echo Instalacao concluida com sucesso!
echo ==========================================
pause
