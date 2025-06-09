@echo off
cd /d %~dp0
echo Current directory: %cd%

:: Add all changes
git add .

:: Commit with message
git commit -m "feat: support random teacher ID mapping and validation warning"

:: Push to main branch
git push origin main

echo Code pushed successfully!
pause
