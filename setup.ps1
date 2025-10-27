# iCast Platform Setup Script
# Windows PowerShell版本

Write-Host "================================" -ForegroundColor Cyan
Write-Host "ICSFP Platform Quick Setup" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# 检查Python版本
Write-Host "Checking Python version..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
Write-Host "  $pythonVersion" -ForegroundColor Green

# 检查pip
Write-Host "`nChecking pip..." -ForegroundColor Yellow
$pipVersion = pip --version 2>&1
Write-Host "  $pipVersion" -ForegroundColor Green

# 安装依赖
Write-Host "`nInstalling dependencies..." -ForegroundColor Yellow
Write-Host "  This may take a few minutes..." -ForegroundColor Gray
pip install -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host "  Dependencies installed successfully!" -ForegroundColor Green
} else {
    Write-Host "  Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# 检查CUDA
Write-Host "`nChecking CUDA availability..." -ForegroundColor Yellow
$cudaCheck = python -c "import torch; print('CUDA available:', torch.cuda.is_available())" 2>&1
Write-Host "  $cudaCheck" -ForegroundColor Green

# 创建必要的目录
Write-Host "`nCreating directories..." -ForegroundColor Yellow
$directories = @("checkpoints", "logs", "results", "data")
foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
        Write-Host "  Created: $dir" -ForegroundColor Green
    } else {
        Write-Host "  Exists: $dir" -ForegroundColor Gray
    }
}

Write-Host "`n================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Cyan

Write-Host "`nQuick Start Commands:" -ForegroundColor Yellow
Write-Host "  python quickstart.py --info      # Show project info" -ForegroundColor White
Write-Host "  python quickstart.py --serve     # Start API server" -ForegroundColor White
Write-Host "  python quickstart.py --test      # Run tests" -ForegroundColor White
Write-Host "  python quickstart.py --train     # Train model" -ForegroundColor White
Write-Host "  python quickstart.py --causal    # Compute causal graph" -ForegroundColor White

Write-Host "`nDocumentation:" -ForegroundColor Yellow
Write-Host "  README_ICAST.md      # Project overview" -ForegroundColor White
Write-Host "  docs/API_GUIDE.md    # API documentation" -ForegroundColor White

Write-Host ""
