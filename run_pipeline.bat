@echo off
REM Script batch pour exécuter le pipeline complet sur Windows

echo ========================================
echo Observatoire des medias - Pipeline
echo ========================================
echo.

python scripts/run_pipeline.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Pipeline termine avec succes !
    echo.
    echo Pour lancer le dashboard:
    echo   python app/api.py
    echo.
) else (
    echo.
    echo Erreur lors de l'execution du pipeline.
    echo.
)

pause

