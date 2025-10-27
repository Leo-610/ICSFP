# ICSFP 简化安装脚本
# 分批安装依赖，避免网络超时

Write-Host "================================" -ForegroundColor Cyan
Write-Host "ICSFP Platform Setup (Simplified)" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "检测到 Python 3.12，将安装兼容版本的包..." -ForegroundColor Yellow
Write-Host ""

# 核心包
Write-Host "步骤 1/5: 安装核心包 (numpy, pandas, scipy)..." -ForegroundColor Yellow
pip install --upgrade numpy pandas scipy --timeout 300

# Web框架
Write-Host "`n步骤 2/5: 安装Web框架 (flask, gunicorn)..." -ForegroundColor Yellow
pip install flask flask-cors gunicorn --timeout 300

# 机器学习
Write-Host "`n步骤 3/5: 安装机器学习包 (scikit-learn, statsmodels)..." -ForegroundColor Yellow
pip install scikit-learn statsmodels --timeout 300

# 可视化
Write-Host "`n步骤 4/5: 安装可视化包 (matplotlib, seaborn)..." -ForegroundColor Yellow
pip install matplotlib seaborn plotly --timeout 300

# 工具包
Write-Host "`n步骤 5/5: 安装工具包 (PyYAML, networkx等)..." -ForegroundColor Yellow
pip install PyYAML omegaconf networkx tqdm --timeout 300

Write-Host "`n================================" -ForegroundColor Cyan
Write-Host "基础包安装完成！" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Cyan

Write-Host "`n注意：PyTorch请根据需要单独安装：" -ForegroundColor Yellow
Write-Host "  CPU版本: pip install torch torchvision torchaudio" -ForegroundColor White
Write-Host "  GPU版本: 访问 https://pytorch.org/ 获取安装命令" -ForegroundColor White

Write-Host "`n快速开始:" -ForegroundColor Yellow
Write-Host "  python quickstart.py --serve" -ForegroundColor White
