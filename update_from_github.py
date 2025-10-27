#!/usr/bin/env python3
"""
从GitHub拉取最新代码并处理版本冲突
"""

import os
import subprocess
import shutil
import logging
from datetime import datetime
import yaml
import json

def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('github_update.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def run_command(command, cwd=None):
    """运行命令并返回结果"""
    logger = logging.getLogger(__name__)
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            cwd=cwd,
            capture_output=True, 
            text=True, 
            check=True
        )
        logger.info(f"命令执行成功: {command}")
        return result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        logger.error(f"命令执行失败: {command}")
        logger.error(f"错误输出: {e.stderr}")
        return None, e.stderr

def backup_current_files():
    """备份当前文件"""
    logger = logging.getLogger(__name__)
    
    backup_dir = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)
    
    # 需要备份的重要文件
    important_files = [
        'config_cmin-cn.yml',
        'config_cmin-us.yml', 
        'config.yml',
        'granger_causality.py',
        'force_retrain_cmin.py',
        'check_cmin_data.py',
        'data/',
        'checkpoints/',
        'log/'
    ]
    
    logger.info(f"备份文件到: {backup_dir}")
    
    for item in important_files:
        if os.path.exists(item):
            if os.path.isdir(item):
                shutil.copytree(item, os.path.join(backup_dir, item))
            else:
                shutil.copy2(item, backup_dir)
            logger.info(f"已备份: {item}")
    
    return backup_dir

def clone_fresh_repo(repo_url, target_dir="HCSF_fresh"):
    """克隆新的仓库"""
    logger = logging.getLogger(__name__)
    
    # 如果目录已存在，删除它
    if os.path.exists(target_dir):
        shutil.rmtree(target_dir)
        logger.info(f"删除现有目录: {target_dir}")
    
    # 克隆仓库
    logger.info(f"克隆仓库: {repo_url}")
    stdout, stderr = run_command(f"git clone {repo_url} {target_dir}")
    
    if stdout is None:
        logger.error("克隆失败")
        return None
    
    logger.info("克隆成功")
    return target_dir

def compare_file_versions(file1, file2):
    """比较两个文件的版本信息"""
    logger = logging.getLogger(__name__)
    
    def get_file_info(filepath):
        if not os.path.exists(filepath):
            return None
        
        stat = os.stat(filepath)
        return {
            'path': filepath,
            'size': stat.st_size,
            'mtime': stat.st_mtime,
            'ctime': stat.st_ctime
        }
    
    info1 = get_file_info(file1)
    info2 = get_file_info(file2)
    
    if info1 is None and info2 is None:
        return "both_missing"
    elif info1 is None:
        return "file1_missing"
    elif info2 is None:
        return "file2_missing"
    else:
        if info1['mtime'] > info2['mtime']:
            return "file1_newer"
        elif info2['mtime'] > info1['mtime']:
            return "file2_newer"
        else:
            return "same_time"

def analyze_config_changes(current_config, fresh_config):
    """分析配置文件的变化"""
    logger = logging.getLogger(__name__)
    
    try:
        with open(current_config, 'r', encoding='utf-8') as f:
            current = yaml.safe_load(f)
    except:
        current = {}
    
    try:
        with open(fresh_config, 'r', encoding='utf-8') as f:
            fresh = yaml.safe_load(f)
    except:
        fresh = {}
    
    changes = {
        'added': [],
        'removed': [],
        'modified': []
    }
    
    # 比较配置项
    all_keys = set(current.keys()) | set(fresh.keys())
    
    for key in all_keys:
        if key not in current:
            changes['added'].append(key)
        elif key not in fresh:
            changes['removed'].append(key)
        elif current[key] != fresh[key]:
            changes['modified'].append(key)
    
    return changes

def merge_configs(current_config, fresh_config, output_config):
    """合并配置文件，保留最新的功能"""
    logger = logging.getLogger(__name__)
    
    try:
        with open(current_config, 'r', encoding='utf-8') as f:
            current = yaml.safe_load(f)
    except:
        current = {}
    
    try:
        with open(fresh_config, 'r', encoding='utf-8') as f:
            fresh = yaml.safe_load(f)
    except:
        fresh = {}
    
    # 合并策略：保留新鲜仓库的配置，但保留当前的数据路径和股票列表
    merged = fresh.copy()
    
    # 保留当前的数据相关配置
    if 'paths' in current:
        merged['paths'] = current['paths']
    
    if 'stocks' in current:
        merged['stocks'] = current['stocks']
    
    if 'dates' in current:
        merged['dates'] = current['dates']
    
    # 保存合并后的配置
    with open(output_config, 'w', encoding='utf-8') as f:
        yaml.dump(merged, f, default_flow_style=False, allow_unicode=True)
    
    logger.info(f"合并配置已保存到: {output_config}")
    return merged

def update_from_github(repo_url="https://github.com/wenrui-jiang/HCSF.git"):
    """从GitHub更新代码的主函数"""
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 60)
    logger.info("从GitHub更新HCSF代码")
    logger.info("=" * 60)
    
    # 1. 备份当前文件
    logger.info("步骤1: 备份当前文件")
    backup_dir = backup_current_files()
    logger.info(f"备份完成: {backup_dir}")
    
    # 2. 克隆新仓库
    logger.info("步骤2: 克隆最新代码")
    fresh_dir = clone_fresh_repo(repo_url)
    if fresh_dir is None:
        logger.error("克隆失败，终止更新")
        return False
    
    # 3. 比较重要文件
    logger.info("步骤3: 比较文件版本")
    important_files = [
        'Main.py',
        'Model.py', 
        'Executor.py',
        'DataPipe.py',
        'ConfigLoader.py',
        'config.yml',
        'requirements.txt'
    ]
    
    file_comparisons = {}
    for filename in important_files:
        current_file = filename
        fresh_file = os.path.join(fresh_dir, filename)
        
        comparison = compare_file_versions(current_file, fresh_file)
        file_comparisons[filename] = comparison
        
        logger.info(f"  {filename}: {comparison}")
    
    # 4. 分析配置文件变化
    logger.info("步骤4: 分析配置文件变化")
    current_config = 'config.yml'
    fresh_config = os.path.join(fresh_dir, 'config.yml')
    
    if os.path.exists(fresh_config):
        config_changes = analyze_config_changes(current_config, fresh_config)
        logger.info(f"配置变化: 新增={len(config_changes['added'])}, "
                   f"删除={len(config_changes['removed'])}, "
                   f"修改={len(config_changes['modified'])}")
        
        if config_changes['modified']:
            logger.info(f"修改的配置项: {config_changes['modified']}")
    
    # 5. 更新文件
    logger.info("步骤5: 更新文件")
    updated_files = []
    
    for filename in important_files:
        current_file = filename
        fresh_file = os.path.join(fresh_dir, filename)
        
        if file_comparisons[filename] in ['file2_newer', 'file1_missing']:
            if os.path.exists(fresh_file):
                shutil.copy2(fresh_file, current_file)
                updated_files.append(filename)
                logger.info(f"已更新: {filename}")
    
    # 6. 合并配置文件
    logger.info("步骤6: 合并配置文件")
    if os.path.exists(fresh_config):
        merge_configs(current_config, fresh_config, 'config_merged.yml')
        logger.info("配置文件已合并为 config_merged.yml")
    
    # 7. 保留自定义文件
    logger.info("步骤7: 保留自定义文件")
    custom_files = [
        'granger_causality.py',
        'force_retrain_cmin.py', 
        'check_cmin_data.py',
        'config_cmin-cn.yml',
        'config_cmin-us.yml'
    ]
    
    for filename in custom_files:
        if os.path.exists(filename):
            logger.info(f"保留自定义文件: {filename}")
    
    # 8. 清理临时目录
    logger.info("步骤8: 清理临时文件")
    shutil.rmtree(fresh_dir)
    logger.info("临时目录已清理")
    
    # 9. 总结
    logger.info("=" * 60)
    logger.info("更新完成!")
    logger.info(f"备份目录: {backup_dir}")
    logger.info(f"更新文件: {updated_files}")
    logger.info("建议:")
    logger.info("1. 检查 config_merged.yml 是否满足需求")
    logger.info("2. 运行 python check_cmin_data.py 验证数据")
    logger.info("3. 运行 python force_retrain_cmin.py 重新训练")
    logger.info("=" * 60)
    
    return True

def main():
    """主函数"""
    logger = setup_logging()
    
    try:
        success = update_from_github()
        if success:
            logger.info("更新成功完成")
        else:
            logger.error("更新失败")
    except Exception as e:
        logger.error(f"更新过程中出现错误: {e}")
        raise

if __name__ == "__main__":
    main()



