@echo off
REM GitHub更新脚本 (Windows版本)
REM 从 https://github.com/wenrui-jiang/HCSF.git 拉取最新代码

echo ==========================================
echo HCSF GitHub更新脚本 (Windows)
echo ==========================================

REM 创建备份目录
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YY=%dt:~2,2%" & set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%" & set "Min=%dt:~10,2%" & set "Sec=%dt:~12,2%"
set "BACKUP_DIR=backup_%YYYY%%MM%%DD%_%HH%%Min%%Sec%"

echo 步骤1: 创建备份目录 %BACKUP_DIR%
mkdir "%BACKUP_DIR%"

echo 步骤2: 备份重要文件
if exist "config_cmin-cn.yml" (
    copy "config_cmin-cn.yml" "%BACKUP_DIR%\"
    echo 已备份 config_cmin-cn.yml
) else (
    echo config_cmin-cn.yml 不存在，跳过
)

if exist "config_cmin-us.yml" (
    copy "config_cmin-us.yml" "%BACKUP_DIR%\"
    echo 已备份 config_cmin-us.yml
) else (
    echo config_cmin-us.yml 不存在，跳过
)

if exist "granger_causality.py" (
    copy "granger_causality.py" "%BACKUP_DIR%\"
    echo 已备份 granger_causality.py
) else (
    echo granger_causality.py 不存在，跳过
)

if exist "force_retrain_cmin.py" (
    copy "force_retrain_cmin.py" "%BACKUP_DIR%\"
    echo 已备份 force_retrain_cmin.py
) else (
    echo force_retrain_cmin.py 不存在，跳过
)

if exist "check_cmin_data.py" (
    copy "check_cmin_data.py" "%BACKUP_DIR%\"
    echo 已备份 check_cmin_data.py
) else (
    echo check_cmin_data.py 不存在，跳过
)

REM 备份数据目录
if exist "data" (
    echo 备份数据目录...
    xcopy "data" "%BACKUP_DIR%\data\" /E /I /Q
)

if exist "checkpoints" (
    echo 备份检查点目录...
    xcopy "checkpoints" "%BACKUP_DIR%\checkpoints\" /E /I /Q
)

if exist "log" (
    echo 备份日志目录...
    xcopy "log" "%BACKUP_DIR%\log\" /E /I /Q
)

echo 备份完成: %BACKUP_DIR%

REM 检查是否已经是Git仓库
if exist ".git" (
    echo 步骤3: 当前目录是Git仓库，拉取最新代码
    
    REM 添加远程仓库（如果还没有）
    git remote | findstr upstream >nul
    if errorlevel 1 (
        echo 添加upstream远程仓库...
        git remote add upstream https://github.com/wenrui-jiang/HCSF.git
    )
    
    REM 获取最新代码
    echo 获取最新代码...
    git fetch upstream
    
    REM 显示差异
    echo 显示与最新代码的差异...
    git diff HEAD upstream/main --name-only
    
    REM 询问是否合并
    set /p merge_choice="是否合并最新代码? (y/n): "
    if /i "%merge_choice%"=="y" (
        echo 合并最新代码...
        git merge upstream/main
        echo 合并完成
    ) else (
        echo 跳过合并
    )
    
) else (
    echo 步骤3: 当前目录不是Git仓库，克隆最新代码
    
    REM 克隆到临时目录
    for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
    set "YY=%dt:~2,2%" & set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
    set "HH=%dt:~8,2%" & set "Min=%dt:~10,2%" & set "Sec=%dt:~12,2%"
    set "TEMP_DIR=HCSF_temp_%YYYY%%MM%%DD%_%HH%%Min%%Sec%"
    
    echo 克隆到临时目录: %TEMP_DIR%
    git clone https://github.com/wenrui-jiang/HCSF.git "%TEMP_DIR%"
    
    echo 步骤4: 比较和更新文件
    
    REM 更新核心文件
    if exist "%TEMP_DIR%\Main.py" (
        if exist "Main.py" (
            echo 更新 Main.py
            copy "%TEMP_DIR%\Main.py" "Main.py"
        ) else (
            echo 添加新文件 Main.py
            copy "%TEMP_DIR%\Main.py" "Main.py"
        )
    )
    
    if exist "%TEMP_DIR%\Model.py" (
        if exist "Model.py" (
            echo 更新 Model.py
            copy "%TEMP_DIR%\Model.py" "Model.py"
        ) else (
            echo 添加新文件 Model.py
            copy "%TEMP_DIR%\Model.py" "Model.py"
        )
    )
    
    if exist "%TEMP_DIR%\Executor.py" (
        if exist "Executor.py" (
            echo 更新 Executor.py
            copy "%TEMP_DIR%\Executor.py" "Executor.py"
        ) else (
            echo 添加新文件 Executor.py
            copy "%TEMP_DIR%\Executor.py" "Executor.py"
        )
    )
    
    if exist "%TEMP_DIR%\DataPipe.py" (
        if exist "DataPipe.py" (
            echo 更新 DataPipe.py
            copy "%TEMP_DIR%\DataPipe.py" "DataPipe.py"
        ) else (
            echo 添加新文件 DataPipe.py
            copy "%TEMP_DIR%\DataPipe.py" "DataPipe.py"
        )
    )
    
    if exist "%TEMP_DIR%\ConfigLoader.py" (
        if exist "ConfigLoader.py" (
            echo 更新 ConfigLoader.py
            copy "%TEMP_DIR%\ConfigLoader.py" "ConfigLoader.py"
        ) else (
            echo 添加新文件 ConfigLoader.py
            copy "%TEMP_DIR%\ConfigLoader.py" "ConfigLoader.py"
        )
    )
    
    if exist "%TEMP_DIR%\requirements.txt" (
        if exist "requirements.txt" (
            echo 更新 requirements.txt
            copy "%TEMP_DIR%\requirements.txt" "requirements.txt"
        ) else (
            echo 添加新文件 requirements.txt
            copy "%TEMP_DIR%\requirements.txt" "requirements.txt"
        )
    )
    
    REM 处理配置文件
    echo 步骤5: 处理配置文件
    if exist "%TEMP_DIR%\config.yml" (
        if exist "config.yml" (
            echo 备份原配置文件...
            copy "config.yml" "%BACKUP_DIR%\config.yml.backup"
            
            echo 创建合并配置文件...
            REM 这里需要Python脚本来合并配置
            echo 请手动检查配置文件差异
        ) else (
            echo 复制新配置文件...
            copy "%TEMP_DIR%\config.yml" "config.yml"
        )
    )
    
    REM 清理临时目录
    echo 步骤6: 清理临时文件
    rmdir /s /q "%TEMP_DIR%"
)

echo ==========================================
echo 更新完成!
echo 备份目录: %BACKUP_DIR%
echo.
echo 下一步建议:
echo 1. 检查配置文件是否正确
echo 2. 运行: python check_cmin_data.py
echo 3. 运行: python force_retrain_cmin.py
echo 4. 重新训练模型
echo ==========================================

pause



