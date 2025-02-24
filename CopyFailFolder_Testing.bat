@echo off

set "SOURCE=D:\Data\Autotest_Inspeccion\Autotest_Inspeccion_1"
set "DEST=D:\Seguimiento_Autotest_temporal"
set "HOSTNAME=%COMPUTERNAME%"
set "DEST_FINAL=%DEST%\%HOSTNAME%"

if not exist "%DEST_FINAL%" (
    mkdir "%DEST_FINAL%"
)

if exist "%SOURCE%\FAIL" (
    :: Usamos la ruta absoluta a robocopy.exe
    ROBOCOPY "%SOURCE%\FAIL" "%DEST_FINAL%\FAIL" /E
    
    echo [OK] Se copio la carpeta "FAIL" correctamente en:
    echo      %DEST_FINAL%\FAIL
) else (
    echo [ERROR] No se encontro la carpeta "fail" en:
    echo        %SOURCE%
)

pause
exit




