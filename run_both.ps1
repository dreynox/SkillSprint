# SkillSprint: Run Frontend + Backend Servers
# Usage: ./run_both.ps1

Write-Host "🚀 Starting SkillSprint..." -ForegroundColor Green
Write-Host ""

# Terminal 1: Frontend server
Write-Host "📱 Starting Frontend Server on port 5500..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd c:\SkillSprint; python -m http.server 5500"

Start-Sleep -Seconds 2

# Terminal 2: Backend server
Write-Host "🔧 Starting Backend API on port 8000..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd c:\SkillSprint; python -m backend.main"

Start-Sleep -Seconds 2

Write-Host ""
Write-Host "✅ Both servers started!" -ForegroundColor Green
Write-Host ""
Write-Host "🔗 Access URLs:" -ForegroundColor Yellow
Write-Host "   Frontend:  http://localhost:5500/frontend/html/signup.html"
Write-Host "   Backend:   http://localhost:8000"
Write-Host "   API Docs:  http://localhost:8000/docs"
Write-Host ""
Write-Host "⚠️  Close the PowerShell windows to stop the servers" -ForegroundColor Yellow
