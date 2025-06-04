@echo off
cd /d %~dp0
echo Current directory: %cd%

:: Add all changes
git add .

:: Commit with default message
git commit -m "feat: update Part1 ranking export"

:: Push to main branch
git push origin main

echo Code pushed successfully!
pause
