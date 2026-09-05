@echo off
cd /d E:\ai-policy\ai-policy
if not exist logs mkdir logs
C:\ProgramData\miniconda3\envs\aipolicy-py\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --workers 1 >> logs\api.stdout.log 2>> logs\api.stderr.log
