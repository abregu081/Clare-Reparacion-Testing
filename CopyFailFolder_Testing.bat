@echo off

set "SOURCE=D:\Data\Autotest_Inspeccion\Autotest_Inspeccion_1"
set "DEST=D:\Seguimiento_Autotest_temporal"
set "HOSTNAME=%COMPUTERNAME%"
set "DEST_FINAL=%DEST%\%HOSTNAME%"

if not exist "%DEST_FINAL%" (
    mkdir "%DEST_FINAL%"
)

:: Copiar la carpeta FAIL y su contenido
if exist "%SOURCE%\FAIL" (
    xcopy "%SOURCE%\FAIL" "%DEST_FINAL%\FAIL" /E /I /H /Y
    echo [OK] Se copio la carpeta "FAIL" correctamente en:
    echo      %DEST_FINAL%\FAIL
) else (
    echo [ERROR] No se encontro la carpeta "FAIL" en:
    echo        %SOURCE%
)

:: Copiar la carpeta PASS y su contenido
if exist "%SOURCE%\PASS" (
    xcopy "%SOURCE%\PASS" "%DEST_FINAL%\PASS" /E /I /H /Y
    echo [OK] Se copio la carpeta "PASS" correctamente en:
    echo      %DEST_FINAL%\PASS
) else (
    echo [ERROR] No se encontro la carpeta "PASS" en:
    echo        %SOURCE%
)

pause
exit

