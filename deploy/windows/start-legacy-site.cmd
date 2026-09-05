@echo off
cd /d E:\zth\backend
if not exist logs mkdir logs
set HOST=127.0.0.1
set PORT=5000
C:\ProgramData\miniconda3\envs\sim\python.exe app0723.py >> logs\legacy.stdout.log 2>> logs\legacy.stderr.log
