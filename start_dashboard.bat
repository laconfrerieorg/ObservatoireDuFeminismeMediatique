@echo off
REM Script batch pour lancer le dashboard web

echo ========================================
echo Observatoire des medias - Dashboard
echo ========================================
echo.
echo Lancement du serveur Flask...
echo.
echo Ouvrez votre navigateur a l'adresse:
echo   http://localhost:5000
echo.
echo Appuyez sur Ctrl+C pour arreter le serveur.
echo.

python app/api.py

pause

