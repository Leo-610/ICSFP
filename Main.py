#!/usr/bin/env python3
import torch
import numpy as np
import argparse
import sys
import os
from Model import Model
from Executor import Executor
from ConfigLoader import logger, stock_symbols
from dataset_manager import DatasetManager


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='PyTorch Stock Prediction with Multi-Dataset Support',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 使用默认数据集训练
  python Main.py
  
  # 使用ACL18数据集训练
  python Main.py --dataset ACL18 --mode train
  
  # 使用CMIN-CN数据集并指定因果发现方法
  python Main.py --dataset CMIN-CN --causal_method cuts_plus
  
  # 只进行测试
  python Main.py --mode test
  
  # 列出所有可用数据集
  python Main.py --list_datasets
  
  # 检查数据集状态
  python Main.py --check_dataset ACL18
  
  # 生成数据集配置文件
  python Main.py --generate_config ACL18
        """
    )
    
    # 数据集相关
    parser.add_argument(
        '--dataset', 
        type=str, 
        default='astock',
        choices=['ACL18', 'CMIN-CN', 'CIKM18', 'astock'],
        help='选择数据集 (默认: astock)'
    )
    
    parser.add_argument(
        '--list_datasets',
        action='store_true',
        help='列出所有可用数据集并退出'
    )
    
    parser.add_argument(
        '--check_dataset',
        type=str,
        metavar='DATASET',
        help='检查指定数据集的状态并退出'
    )
    
    parser.add_argument(
        '--generate_config',
        type=str,
        metavar='DATASET',
        help='为指定数据集生成配置文件并退出'
    )
    
    # 运行模式
    parser.add_argument(
        '--mode',
        type=str,
        default='train',
        choices=['train', 'test', 'train_test'],
        help='运行模式: train(仅训练), test(仅测试), train_test(训练+测试) (默认: train)'
    )
    
    # 因果发现方法
    parser.add_argument(
        '--causal_method',
        type=str,
        default='granger',
        choices=['granger', 'cuts_plus', 'transfer_entropy', 'none'],
        help='因果发现方法 (默认: granger)'
    )
    
    parser.add_argument(
        '--recompute_causal',
        action='store_true',
        help='强制重新计算因果图'
    )
    
    # 训练参数
    parser.add_argument(
        '--epochs',
        type=int,
        default=15,
        help='训练轮数 (默认: 15)'
    )
    
    parser.add_argument(
        '--batch_size',
        type=int,
        default=32,
        help='批次大小 (默认: 32)'
    )
    
    parser.add_argument(
        '--learning_rate',
        type=float,
        default=0.001,
        help='学习率 (默认: 0.001)'
    )
    
    # 设备
    parser.add_argument(
        '--device',
        type=str,
        default='auto',
        choices=['auto', 'cuda', 'cpu'],
        help='计算设备 (默认: auto - 自动选择)'
    )
    
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='随机种子 (默认: 42)'
    )
    
    return parser.parse_args()


def load_causal_graph(args=None, force_recompute=False):
    """
    加载或生成因果图
    
    Args:
        args: 命令行参数
        force_recompute: 是否强制重新计算
    """
    causal_method = args.causal_method if args else 'granger'
    
    # 根据因果方法确定文件名
    if causal_method == 'none':
        logger.info('Causal discovery disabled (--causal_method none)')
        return None
    
    graph_file = f'causal_graph_{causal_method}.npy'
    if causal_method == 'granger':
        graph_file = 'causal_graph.npy'  # 保持向后兼容
    
    # 如果强制重新计算,删除现有文件
    if force_recompute and os.path.exists(graph_file):
        logger.info(f'Force recomputing causal graph (--recompute_causal)')
        os.remove(graph_file)
    
    try:
        # 尝试从文件加载因果图
        graph = np.load(graph_file)
        logger.info(f'✅ Causal graph loaded from {graph_file}')
        logger.info(f'   Shape: {graph.shape}')
        logger.info(f'   Method: {causal_method}')
        logger.info(f'   Sparsity: {np.count_nonzero(graph) / graph.size:.3f}')
        return graph
    except FileNotFoundError:
        logger.warning(f'⚠️  Causal graph file not found: {graph_file}')
        
        # 提示用户运行因果发现
        if causal_method == 'granger':
            logger.info('💡 运行因果发现: python granger_causality.py')
        elif causal_method == 'cuts_plus':
            logger.info('💡 运行因果发现: python compute_cuts_graph.py')
        elif causal_method == 'transfer_entropy':
            logger.warning('⚠️  Transfer Entropy未实现,请使用granger或cuts_plus')
        
        logger.info('📝 正在生成随机因果图用于测试...')
        # 如果文件不存在，生成一个示例因果图
        n_stocks = len(stock_symbols)  # 90只股票

        # 生成稀疏的因果图矩阵
        graph = np.random.random((n_stocks, n_stocks))

        # 使其稀疏化（大部分元素为0）
        threshold = 0.8  # 只保留20%的连接
        graph = np.where(graph > threshold, graph, 0.0)

        # 对角线设为0（股票不影响自己）
        np.fill_diagonal(graph, 0.0)

        # 归一化每行，使其和为1
        row_sums = graph.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1  # 避免除零
        graph = graph / row_sums

        logger.info(f'Generated random causal graph with shape: {graph.shape}')
        logger.info(f'Sparsity: {np.count_nonzero(graph) / graph.size:.3f}')

        # 保存生成的图以供后续使用
        np.save('causal_graph.npy', graph)

    return graph


def setup_device(args=None):
    """
    设置计算设备
    
    Args:
        args: 命令行参数
    """
    device_choice = args.device if args else 'auto'
    
    if device_choice == 'cpu':
        device = 'cpu'
        logger.info('🖥️  Using CPU (forced by --device cpu)')
    elif device_choice == 'cuda':
        if torch.cuda.is_available():
            device = 'cuda'
            logger.info(f'🚀 Using GPU: {torch.cuda.get_device_name(0)}')
            logger.info(f'   Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB')
        else:
            logger.warning('⚠️  CUDA not available, falling back to CPU')
            device = 'cpu'
    else:  # auto
        if torch.cuda.is_available():
            device = 'cuda'
            logger.info(f'🚀 Using GPU: {torch.cuda.get_device_name(0)}')
            logger.info(f'   Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB')
        else:
            device = 'cpu'
            logger.info('🖥️  Using CPU')

    return device


def print_model_info(model):
    """打印模型信息"""
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)

    logger.info(f'Model: {model.model_name}')
    logger.info(f'Total parameters: {total_params:,}')
    logger.info(f'Trainable parameters: {trainable_params:,}')

    if model.graph is not None:
        logger.info(f'Causal graph shape: {model.graph.shape}')
        logger.info(f'Causal variables dimension: {model.causal_z_size}')


def main():
    """主函数"""
    # 解析命令行参数
    args = parse_args()
    
    # 创建数据集管理器
    manager = DatasetManager()
    
    # 处理数据集管理命令
    if args.list_datasets:
        manager.list_datasets(verbose=True)
        return
    
    if args.check_dataset:
        logger.info('='*80)
        logger.info(f'检查数据集: {args.check_dataset}')
        logger.info('='*80)
        summary = manager.get_summary(args.check_dataset)
        print(summary)
        return
    
    if args.generate_config:
        logger.info('='*80)
        logger.info(f'生成配置文件: {args.generate_config}')
        logger.info('='*80)
        manager.generate_config(args.generate_config)
        return
    
    # 显示启动信息
    logger.info('='*80)
    logger.info('🚀 PyTorch Stock Prediction - Multi-Dataset System')
    logger.info('='*80)
    
    # 设置随机种子
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(args.seed)
    logger.info(f'🎲 Random seed: {args.seed}')
    
    # 1. 数据集配置
    logger.info('='*80)
    logger.info('📊 数据集配置')
    logger.info('='*80)
    dataset_config = manager.get_dataset(args.dataset)
    logger.info(f'数据集: {dataset_config["full_name"]}')
    logger.info(f'描述: {dataset_config["description"]}')
    logger.info(f'股票数: {dataset_config["stocks"]}')
    logger.info(f'时间范围: {dataset_config["date_range"]["start"]} ~ {dataset_config["date_range"]["end"]}')
    
    # 检查数据集是否就绪
    check = manager.check_dataset(args.dataset)
    if not check['ready']:
        logger.error('❌ 数据集未就绪!')
        logger.error(f'   价格数据: {"✅" if check["price_exists"] else "❌"} ({check["price_count"]} 文件)')
        logger.error(f'   文本数据: {"✅" if check["text_exists"] else "❌"} ({check["text_count"]} 目录)')
        logger.error('💡 提示: 运行 python download_cmin_dataset.py 准备数据')
        sys.exit(1)
    
    logger.info(f'✅ 数据集就绪 ({check["price_count"]} 价格文件, {check["text_count"]} 文本目录)')

    # 2. 设置设备
    logger.info('='*80)
    logger.info('🔧 设备配置')
    logger.info('='*80)
    device = setup_device(args)

    # 3. 加载因果图
    logger.info('='*80)
    logger.info('🔗 因果图配置')
    logger.info('='*80)
    logger.info(f'因果发现方法: {args.causal_method}')
    graph = load_causal_graph(args, force_recompute=args.recompute_causal)

    # 4. 创建模型
    logger.info('='*80)
    logger.info('🤖 模型配置')
    logger.info('='*80)
    model = Model(graph=graph)
    print_model_info(model)

    # 5. 设置训练参数
    silence_step = 0
    skip_step = 20

    # 6. 创建执行器
    logger.info('='*80)
    logger.info('⚙️  执行器配置')
    logger.info('='*80)
    logger.info(f'模式: {args.mode}')
    logger.info(f'批次大小: {args.batch_size}')
    logger.info(f'学习率: {args.learning_rate}')
    logger.info(f'训练轮数: {args.epochs}')
    
    exe = Executor(model, silence_step=silence_step, skip_step=skip_step, device=device)

    # 7. 执行训练/测试
    try:
        if args.mode in ['train', 'train_test']:
            logger.info('='*80)
            logger.info('🎓 开始训练')
            logger.info('='*80)
            exe.train_and_dev()
            logger.info('✅ 训练完成!')

        if args.mode in ['test', 'train_test']:
            logger.info('='*80)
            logger.info('🧪 开始测试')
            logger.info('='*80)
            exe.restore_and_test()
            logger.info('✅ 测试完成!')

    except KeyboardInterrupt:
        logger.warning('⚠️  训练被用户中断')
    except Exception as e:
        logger.error(f'❌ 执行失败: {e}')
        raise

    logger.info('='*80)
    logger.info('🎉 程序执行完成')
    logger.info('='*80)


if __name__ == '__main__':
    main()