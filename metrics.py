#!/usr/bin/env python3
import torch
import numpy as np
import math


def n_accurate_numpy(y, y_):
    """
    计算准确预测数量 (numpy版本)
    Args:
        y: 预测结果 [batch_size, y_size]
        y_: 真实标签 [batch_size, y_size]
    Returns:
        准确预测的数量
    """
    pred_classes = np.argmax(y, axis=1)
    true_classes = np.argmax(y_, axis=1)
    return np.sum(pred_classes == true_classes)


def n_accurate_torch(y, y_):
    """
    计算准确预测数量 (torch版本)
    Args:
        y: 预测结果 [batch_size, y_size]
        y_: 真实标签 [batch_size, y_size]
    Returns:
        准确预测的数量
    """
    pred_classes = torch.argmax(y, dim=1)
    true_classes = torch.argmax(y_, dim=1)
    return torch.sum(pred_classes == true_classes).item()


def eval_acc(n_acc, total):
    """计算准确率"""
    return float(n_acc) / total if total > 0 else 0.0


def create_confusion_matrix(y, y_, is_distribution=True):
    """
    创建混淆矩阵
    Args:
        y: 预测结果
        y_: 真实标签
        is_distribution: 是否是概率分布格式
    Returns:
        tp, fp, tn, fn
    """
    if isinstance(y, torch.Tensor):
        y = y.cpu().numpy()
    if isinstance(y_, torch.Tensor):
        y_ = y_.cpu().numpy()

    n_samples = float(y_.shape[0])

    if is_distribution:
        label_ref = np.argmax(y_, axis=1)  # 真实标签
        label_hyp = np.argmax(y, axis=1)   # 预测标签
    else:
        label_ref, label_hyp = y_, y

    # 预测为正例和负例的数量
    p_in_hyp = np.sum(label_hyp)
    n_in_hyp = n_samples - p_in_hyp

    # True Positive: 预测为正例且实际为正例
    tp = np.sum(np.multiply(label_ref, label_hyp))
    # False Positive: 预测为正例但实际为负例
    fp = p_in_hyp - tp

    # True Negative: 预测为负例且实际为负例
    tn = n_samples - np.count_nonzero(label_ref + label_hyp)
    # False Negative: 预测为负例但实际为正例
    fn = n_in_hyp - tn

    return float(tp), float(fp), float(tn), float(fn)


def eval_mcc(tp, fp, tn, fn):
    """
    计算Matthews相关系数
    MCC = (TP×TN - FP×FN) / sqrt((TP+FP)(TP+FN)(TN+FP)(TN+FN))
    """
    denominator = (tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)
    if denominator == 0:
        return None
    return (tp * tn - fp * fn) / math.sqrt(denominator)


def eval_precision_recall_f1(tp, fp, tn, fn):
    """计算精确率、召回率和F1分数"""
    # 精确率: TP / (TP + FP)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0

    # 召回率: TP / (TP + FN)
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0

    # F1分数: 2 * (precision * recall) / (precision + recall)
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return precision, recall, f1


def eval_res(gen_n_acc, gen_size, gen_loss_list, y_list, y_list_, use_mcc=None):
    """
    评估结果统计
    Args:
        gen_n_acc: 总正确预测数
        gen_size: 总样本数
        gen_loss_list: 损失列表
        y_list: 预测结果列表
        y_list_: 真实标签列表
        use_mcc: 是否计算MCC
    Returns:
        结果字典
    """
    gen_acc = eval_acc(n_acc=gen_n_acc, total=gen_size)
    gen_loss = np.mean(gen_loss_list)

    results = {
        'loss': gen_loss,
        'acc': gen_acc,
    }

    if use_mcc and len(y_list) > 0 and len(y_list_) > 0:
        # 合并所有预测结果
        gen_y = np.vstack(y_list)
        gen_y_ = np.vstack(y_list_)

        # 计算混淆矩阵
        tp, fp, tn, fn = create_confusion_matrix(y=gen_y, y_=gen_y_)

        # 计算各种指标
        mcc = eval_mcc(tp, fp, tn, fn)
        precision, recall, f1 = eval_precision_recall_f1(tp, fp, tn, fn)

        results.update({
            'mcc': mcc,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'tp': tp,
            'fp': fp,
            'tn': tn,
            'fn': fn
        })

    return results


def basic_train_stat(train_batch_loss_list, train_epoch_n_acc, train_epoch_size):
    """
    计算训练epoch统计
    Args:
        train_batch_loss_list: 训练批次损失列表
        train_epoch_n_acc: epoch总正确数
        train_epoch_size: epoch总样本数
    Returns:
        epoch平均损失, epoch准确率
    """
    train_epoch_loss = np.mean(train_batch_loss_list)
    train_epoch_acc = eval_acc(n_acc=train_epoch_n_acc, total=train_epoch_size)
    return train_epoch_loss, train_epoch_acc


def calculate_sharpe_ratio(returns, risk_free_rate=0.0):
    """
    计算夏普比率 (金融指标)
    Args:
        returns: 收益率序列
        risk_free_rate: 无风险收益率
    Returns:
        夏普比率
    """
    if isinstance(returns, torch.Tensor):
        returns = returns.cpu().numpy()

    excess_returns = returns - risk_free_rate
    if np.std(excess_returns) == 0:
        return 0.0
    return np.mean(excess_returns) / np.std(excess_returns)


def calculate_max_drawdown(cumulative_returns):
    """
    计算最大回撤
    Args:
        cumulative_returns: 累积收益率序列
    Returns:
        最大回撤
    """
    if isinstance(cumulative_returns, torch.Tensor):
        cumulative_returns = cumulative_returns.cpu().numpy()

    peak = np.maximum.accumulate(cumulative_returns)
    drawdown = (cumulative_returns - peak) / peak
    return np.min(drawdown)


def evaluate_trading_strategy(predictions, actual_returns, transaction_cost=0.001):
    """
    评估交易策略表现
    Args:
        predictions: 预测结果 [n_samples, 2] (下跌概率, 上涨概率)
        actual_returns: 实际收益率 [n_samples]
        transaction_cost: 交易成本
    Returns:
        策略评估结果
    """
    if isinstance(predictions, torch.Tensor):
        predictions = predictions.cpu().numpy()
    if isinstance(actual_returns, torch.Tensor):
        actual_returns = actual_returns.cpu().numpy()

    # 根据预测生成交易信号
    # 如果预测上涨概率 > 0.5，买入(1)，否则卖出(-1)
    signals = np.where(predictions[:, 1] > 0.5, 1, -1)

    # 计算策略收益（扣除交易成本）
    strategy_returns = signals * actual_returns - np.abs(np.diff(np.concatenate([[0], signals]))) * transaction_cost

    # 计算累积收益
    cumulative_returns = np.cumprod(1 + strategy_returns)

    # 计算各种指标
    total_return = cumulative_returns[-1] - 1
    annualized_return = (1 + total_return) ** (252 / len(strategy_returns)) - 1  # 假设252个交易日
    volatility = np.std(strategy_returns) * np.sqrt(252)
    sharpe_ratio = calculate_sharpe_ratio(strategy_returns)
    max_drawdown = calculate_max_drawdown(cumulative_returns)

    # 计算胜率
    win_rate = np.sum(strategy_returns > 0) / len(strategy_returns)

    # 计算信息比率 (相对于基准的超额收益)
    benchmark_return = np.mean(actual_returns)  # 简单基准：平均收益
    excess_returns = strategy_returns - benchmark_return
    information_ratio = np.mean(excess_returns) / np.std(excess_returns) if np.std(excess_returns) > 0 else 0.0

    return {
        'total_return': total_return,
        'annualized_return': annualized_return,
        'volatility': volatility,
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown,
        'win_rate': win_rate,
        'information_ratio': information_ratio,
        'n_trades': np.sum(np.abs(np.diff(np.concatenate([[0], signals])))) // 2,
        'strategy_returns': strategy_returns,
        'cumulative_returns': cumulative_returns
    }