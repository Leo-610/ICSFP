#!/usr/bin/env python3
"""
强制重新训练CMIN数据集的脚本
解决模型加载和数据问题
"""

import os
import shutil
import yaml
import numpy as np
import pandas as pd
from datetime import datetime
import logging

def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('force_retrain.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def clear_old_checkpoints(checkpoint_dir):
    """清除旧的检查点文件"""
    logger = logging.getLogger(__name__)
    
    if os.path.exists(checkpoint_dir):
        logger.info(f"清除旧的检查点目录: {checkpoint_dir}")
        shutil.rmtree(checkpoint_dir)
        logger.info("旧检查点已清除")
    else:
        logger.info("没有找到旧的检查点目录")

def verify_data_integrity(data_path, config_path):
    """验证数据完整性"""
    logger = logging.getLogger(__name__)
    
    # 加载配置
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    stock_list = config['stocks']['cmin']
    logger.info(f"配置文件中定义了 {len(stock_list)} 只股票")
    
    # 检查数据文件
    missing_files = []
    valid_files = []
    
    for stock in stock_list:
        file_path = os.path.join(data_path, f'{stock}.txt')
        if os.path.exists(file_path):
            try:
                # 检查文件内容
                df = pd.read_csv(file_path, sep='\t', header=None, 
                               names=['date', 'return', 'volume', 'high', 'low', 'close'])
                
                if len(df) > 100 and not df['return'].isna().all():
                    valid_files.append(stock)
                else:
                    logger.warning(f"文件 {stock}.txt 数据不足或全为NaN")
            except Exception as e:
                logger.error(f"读取文件 {stock}.txt 失败: {e}")
        else:
            missing_files.append(stock)
    
    logger.info(f"有效数据文件: {len(valid_files)}")
    logger.info(f"缺失文件: {len(missing_files)}")
    
    if len(missing_files) > 0:
        logger.warning(f"缺失文件示例: {missing_files[:5]}")
    
    return valid_files, missing_files

def create_clean_config(config_path, valid_stocks, output_path):
    """创建只包含有效股票的配置文件"""
    logger = logging.getLogger(__name__)
    
    # 加载原配置
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 更新股票列表
    config['stocks']['cmin'] = valid_stocks
    
    # 确保路径正确
    config['paths']['price'] = 'data/preprocessed_cmin-cn'
    
    # 保存新配置
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
    
    logger.info(f"新配置文件已保存到: {output_path}")
    logger.info(f"包含 {len(valid_stocks)} 只有效股票")

def run_granger_analysis(data_path, valid_stocks, output_path='granger_results.npz'):
    """运行Granger因果分析"""
    logger = logging.getLogger(__name__)
    
    try:
        from granger_causality import GrangerCausalityAnalyzer
        
        logger.info("开始Granger因果分析...")
        
        # 加载数据
        data_list = []
        stock_names = []
        
        for stock in valid_stocks[:50]:  # 限制数量避免计算量过大
            file_path = os.path.join(data_path, f'{stock}.txt')
            try:
                df = pd.read_csv(file_path, sep='\t', header=None, 
                               names=['date', 'return', 'volume', 'high', 'low', 'close'])
                
                returns = df['return'].values
                if len(returns) > 100:
                    data_list.append(returns)
                    stock_names.append(stock)
            except Exception as e:
                logger.error(f"读取 {stock} 失败: {e}")
                continue
        
        if len(data_list) < 2:
            logger.error("有效数据不足，无法进行因果分析")
            return None
        
        # 对齐数据
        min_length = min(len(data) for data in data_list)
        aligned_data = np.array([data[:min_length] for data in data_list]).T
        
        logger.info(f"数据形状: {aligned_data.shape}")
        
        # 运行分析
        analyzer = GrangerCausalityAnalyzer(max_lags=3, significance_level=0.05)
        causality_matrix, p_values = analyzer.compute_causality_matrix(
            aligned_data, stock_names
        )
        
        # 保存结果
        analyzer.save_results(output_path)
        
        # 显示结果
        top_relationships = analyzer.get_top_causal_relationships(top_k=10)
        logger.info("前10个最强的因果关系:")
        for i, rel in enumerate(top_relationships, 1):
            logger.info(f"{i:2d}. {rel['cause']} -> {rel['effect']}: "
                       f"p={rel['p_value']:.4f}")
        
        return analyzer
        
    except ImportError:
        logger.error("无法导入granger_causality模块")
        return None
    except Exception as e:
        logger.error(f"Granger分析失败: {e}")
        return None

def main():
    """主函数"""
    logger = setup_logging()
    
    logger.info("=" * 60)
    logger.info("强制重新训练CMIN数据集")
    logger.info("=" * 60)
    
    # 配置路径
    config_path = 'config_cmin-cn.yml'
    data_path = 'data/preprocessed_cmin-cn'
    checkpoint_dir = 'checkpoints'
    
    # 1. 清除旧检查点
    logger.info("步骤1: 清除旧检查点")
    clear_old_checkpoints(checkpoint_dir)
    
    # 2. 验证数据完整性
    logger.info("步骤2: 验证数据完整性")
    valid_stocks, missing_stocks = verify_data_integrity(data_path, config_path)
    
    if len(valid_stocks) < 10:
        logger.error("有效股票数量不足，请检查数据文件")
        return
    
    # 3. 创建干净的配置文件
    logger.info("步骤3: 创建干净的配置文件")
    clean_config_path = 'config_cmin-cn_clean.yml'
    create_clean_config(config_path, valid_stocks, clean_config_path)
    
    # 4. 运行Granger因果分析
    logger.info("步骤4: 运行Granger因果分析")
    analyzer = run_granger_analysis(data_path, valid_stocks)
    
    # 5. 提供重新训练的建议
    logger.info("步骤5: 重新训练建议")
    logger.info("现在可以运行以下命令重新训练:")
    logger.info(f"export HCSF_CONFIG={clean_config_path}")
    logger.info("python Main.py")
    
    logger.info("=" * 60)
    logger.info("准备完成！")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()





