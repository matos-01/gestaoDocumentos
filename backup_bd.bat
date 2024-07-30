@echo off
for /f "tokens=1-4 delims=/ " %%i in ("%date%") do (

     echo %%i
     set dow=%%i
     
     set month=%%j
     
     set day=%%k
     
     set year=%%l
)

set datestr=%dow%_%month%_%day%

pg_dump --dbname=postgresql://postgres:M4N4G3R!@localhost:5433/panflight > "F:\OneDrive - Panflight\GESTOR\panflight_backup_%datestr%.sql"