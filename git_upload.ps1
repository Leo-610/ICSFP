# ICSFP Upload Script
# Fix 403 error

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "ICSFP GitHub Upload Script" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Check current branch
Write-Host "[1/5] Checking current branch..." -ForegroundColor Yellow
git branch --show-current

# Switch to main branch
Write-Host ""
Write-Host "[2/5] Switching to main branch..." -ForegroundColor Yellow
git branch -M main

# Show remote repositories
Write-Host ""
Write-Host "[3/5] Current remote configuration..." -ForegroundColor Yellow
git remote -v

# Push (will trigger Git Credential Manager)
Write-Host ""
Write-Host "[4/5] Pushing to GitHub..." -ForegroundColor Yellow
Write-Host "Note: If login window appears, use your GitHub credentials" -ForegroundColor Green
Write-Host ""

# Use URL without token, let Git Credential Manager handle authentication
git remote set-url icsfp https://github.com/Leo-610/ICSFP.git
git push -u icsfp main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "==================================" -ForegroundColor Green
    Write-Host "SUCCESS!" -ForegroundColor Green
    Write-Host "==================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Visit your repository:" -ForegroundColor Cyan
    Write-Host "https://github.com/Leo-610/ICSFP" -ForegroundColor Blue
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "==================================" -ForegroundColor Red
    Write-Host "UPLOAD FAILED" -ForegroundColor Red
    Write-Host "==================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Try these solutions:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Solution 1: Use GitHub Desktop (Easiest)" -ForegroundColor Cyan
    Write-Host "  1. Download: https://desktop.github.com/" -ForegroundColor White
    Write-Host "  2. Login to GitHub" -ForegroundColor White
    Write-Host "  3. File -> Add Local Repository" -ForegroundColor White
    Write-Host "  4. Publish repository" -ForegroundColor White
    Write-Host ""
    Write-Host "Solution 2: Check Token Permissions" -ForegroundColor Cyan
    Write-Host "  1. Visit: https://github.com/settings/tokens" -ForegroundColor White
    Write-Host "  2. Ensure token has full 'repo' permission" -ForegroundColor White
    Write-Host "  3. Generate new token and use it" -ForegroundColor White
    Write-Host ""
    Write-Host "Solution 3: Upload via GitHub Web" -ForegroundColor Cyan
    Write-Host "  1. Compress HCSF folder to zip" -ForegroundColor White
    Write-Host "  2. Visit: https://github.com/Leo-610/ICSFP" -ForegroundColor White
    Write-Host "  3. Upload zip file" -ForegroundColor White
    Write-Host ""
}

Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
