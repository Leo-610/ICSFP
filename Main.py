#!/usr/bin/env python3
import torch
import numpy as np
from Model import Model
from Executor import Executor
from ConfigLoader import logger, stock_symbols


def load_causal_graph():
    """
    加载或生成因果图
    这里假设因果图已经计算好并保存为numpy文件
    如果没有，可以用随机矩阵代替进行测试
    """
    try:
        # 尝试从文件加载因果图
        graph = np.load('causal_graph.npy')
        logger.info(f'Causal graph loaded with shape: {graph.shape}')
    except FileNotFoundError:
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


def setup_device():
    """设置计算设备"""
    if torch.cuda.is_available():
        device = 'cuda'
        logger.info(f'Using GPU: {torch.cuda.get_device_name(0)}')
        logger.info(f'GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB')
    else:
        device = 'cpu'
        logger.info('Using CPU')

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
    logger.info('='*60)
    logger.info('PyTorch Stock Prediction with Causal Graph')
    logger.info('='*60)

    # 1. 设置设备
    device = setup_device()

    # 2. 加载因果图
    logger.info('Loading causal graph...')
    graph = load_causal_graph()

    # 3. 创建模型
    logger.info('Creating model...')
    model = Model(graph=graph)

    # 4. 打印模型信息
    print_model_info(model)

    # 5. 设置训练参数
    silence_step = 0
    skip_step = 20

    # 6. 创建执行器
    logger.info('Creating executor...')
    exe = Executor(model, silence_step=silence_step, skip_step=skip_step, device=device)

    # 7. 开始训练
    logger.info('Starting training...')
    try:
        exe.train_and_dev()
        logger.info('Training completed successfully!')

        # 8. 测试
        logger.info('Starting testing...')
        exe.restore_and_test()
        logger.info('Testing completed successfully!')

    except KeyboardInterrupt:
        logger.info('Training interrupted by user')
    except Exception as e:
        logger.error(f'Training failed with error: {e}')
        raise

    logger.info('='*60)
    logger.info('Program finished')
    logger.info('='*60)


if __name__ == '__main__':
    # 设置随机种子以确保可重现性
    torch.manual_seed(42)
    np.random.seed(42)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(42)

    main()