@echo off
chcp 65001 >nul
set PYTHON=%USERPROFILE%\.workbuddy\binaries\python\versions\3.11.9\python.exe
echo 🦅 处理新增剧本 Day 18~40...
%PYTHON% "%~dp0run_pipeline.py" --day-range 18 40
echo Done
