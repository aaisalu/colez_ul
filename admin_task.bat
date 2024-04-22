@ECHO OFF

echo Current directory: %cd%
cmd /k "cd /d %~dp0\venv\Scripts & activate & cd /d %~dp0\modules & python verify_admin.py admin_level & exit"
SET EXIT_CODE=%ERRORLEVEL%
cd %~dp0\
echo  %EXIT_CODE%
echo %cd%
Ping www.google.com -n 2 -w 1000 >NUL 2>&1

@REM IF %EXIT_CODE% neq 1 (
@REM     echo yes
@REM     Ping www.google.com -n 5 -w 1000 >NUL 2>&1
@REM ) ELSE (
@REM     echo no
@REM     Ping www.google.com -n 5 -w 1000 >NUL 2>&1

@REM )