#!/bin/bash

# GitHub更新脚本
# 从 https://github.com/wenrui-jiang/HCSF.git 拉取最新代码

set -e  # 遇到错误立即退出

echo "=========================================="
echo "HCSF GitHub更新脚本"
echo "=========================================="

# 创建备份
BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
echo "步骤1: 创建备份目录 $BACKUP_DIR"
mkdir -p "$BACKUP_DIR"

# 备份重要文件
echo "步骤2: 备份重要文件"
cp config_cmin-cn.yml "$BACKUP_DIR/" 2>/dev/null || echo "config_cmin-cn.yml 不存在，跳过"
cp config_cmin-us.yml "$BACKUP_DIR/" 2>/dev/null || echo "config_cmin-us.yml 不存在，跳过"
cp granger_causality.py "$BACKUP_DIR/" 2>/dev/null || echo "granger_causality.py 不存在，跳过"
cp force_retrain_cmin.py "$BACKUP_DIR/" 2>/dev/null || echo "force_retrain_cmin.py 不存在，跳过"
cp check_cmin_data.py "$BACKUP_DIR/" 2>/dev/null || echo "check_cmin_data.py 不存在，跳过"

# 备份数据目录
if [ -d "data" ]; then
    echo "备份数据目录..."
    cp -r data "$BACKUP_DIR/"
fi

if [ -d "checkpoints" ]; then
    echo "备份检查点目录..."
    cp -r checkpoints "$BACKUP_DIR/"
fi

if [ -d "log" ]; then
    echo "备份日志目录..."
    cp -r log "$BACKUP_DIR/"
fi

echo "备份完成: $BACKUP_DIR"

# 检查是否已经是Git仓库
if [ -d ".git" ]; then
    echo "步骤3: 当前目录是Git仓库，拉取最新代码"
    
    # 添加远程仓库（如果还没有）
    if ! git remote | grep -q upstream; then
        echo "添加upstream远程仓库..."
        git remote add upstream https://github.com/wenrui-jiang/HCSF.git
    fi
    
    # 获取最新代码
    echo "获取最新代码..."
    git fetch upstream
    
    # 显示差异
    echo "显示与最新代码的差异..."
    git diff HEAD upstream/main --name-only
    
    # 询问是否合并
    read -p "是否合并最新代码? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "合并最新代码..."
        git merge upstream/main
        echo "合并完成"
    else
        echo "跳过合并"
    fi
    
else
    echo "步骤3: 当前目录不是Git仓库，克隆最新代码"
    
    # 克隆到临时目录
    TEMP_DIR="HCSF_temp_$(date +%Y%m%d_%H%M%S)"
    echo "克隆到临时目录: $TEMP_DIR"
    git clone https://github.com/wenrui-jiang/HCSF.git "$TEMP_DIR"
    
    # 比较文件并更新
    echo "步骤4: 比较和更新文件"
    
    # 需要更新的文件列表
    FILES_TO_UPDATE=(
        "Main.py"
        "Model.py"
        "Executor.py"
        "DataPipe.py"
        "ConfigLoader.py"
        "requirements.txt"
    )
    
    for file in "${FILES_TO_UPDATE[@]}"; do
        if [ -f "$TEMP_DIR/$file" ]; then
            if [ -f "$file" ]; then
                # 比较文件时间戳
                if [ "$TEMP_DIR/$file" -nt "$file" ]; then
                    echo "更新 $file (GitHub版本更新)"
                    cp "$TEMP_DIR/$file" "$file"
                else
                    echo "跳过 $file (本地版本更新或相同)"
                fi
            else
                echo "添加新文件 $file"
                cp "$TEMP_DIR/$file" "$file"
            fi
        fi
    done
    
    # 处理配置文件
    echo "步骤5: 处理配置文件"
    if [ -f "$TEMP_DIR/config.yml" ]; then
        if [ -f "config.yml" ]; then
            echo "备份原配置文件..."
            cp config.yml "$BACKUP_DIR/config.yml.backup"
            
            echo "比较配置文件差异..."
            if ! diff -q config.yml "$TEMP_DIR/config.yml" > /dev/null; then
                echo "配置文件有差异，创建合并版本..."
                
                # 创建合并版本（保留数据配置，更新模型配置）
                python3 -c "
import yaml
import sys

# 加载当前配置
with open('config.yml', 'r', encoding='utf-8') as f:
    current = yaml.safe_load(f)

# 加载GitHub配置
with open('$TEMP_DIR/config.yml', 'r', encoding='utf-8') as f:
    github = yaml.safe_load(f)

# 合并配置：保留数据相关，更新模型相关
merged = github.copy()
if 'paths' in current:
    merged['paths'] = current['paths']
if 'stocks' in current:
    merged['stocks'] = current['stocks']
if 'dates' in current:
    merged['dates'] = current['dates']

# 保存合并配置
with open('config_merged.yml', 'w', encoding='utf-8') as f:
    yaml.dump(merged, f, default_flow_style=False, allow_unicode=True)

print('配置文件已合并为 config_merged.yml')
"
            else
                echo "配置文件相同，无需更新"
            fi
        else
            echo "复制新配置文件..."
            cp "$TEMP_DIR/config.yml" "config.yml"
        fi
    fi
    
    # 清理临时目录
    echo "步骤6: 清理临时文件"
    rm -rf "$TEMP_DIR"
fi

echo "=========================================="
echo "更新完成!"
echo "备份目录: $BACKUP_DIR"
echo ""
echo "下一步建议:"
echo "1. 检查配置文件是否正确"
echo "2. 运行: python check_cmin_data.py"
echo "3. 运行: python force_retrain_cmin.py"
echo "4. 重新训练模型"
echo "=========================================="



