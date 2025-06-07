@echo off
cd /d %~dp0
echo Current directory: %cd%

:: Add all changes
git add .

:: Commit with default message
git commit -m "feat: clean LaTeX and add real data"

:: Push to main branch
git push origin main

echo Code pushed successfully!
pause
