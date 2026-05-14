#!/usr/bin/env python3
"""
滚动窗口 Granger 因果图计算脚本
================================
将训练集（2020-01-02 ~ 2024-04-08）按滚动窗口分段，
每段计算一次 Granger 因果图，代替单一静态图。

算法：
  - 窗口大小（WINDOW_DAYS）：90 个日历天
  - 滑动步长（STEP_DAYS）   ：30 个日历天
  - 对窗口内每对股票做 Granger F 检验（max_lags=5），
    权重 = (1 - p_value) * (p_value < SIG_LEVEL)
  - 行归一化后保存

输出：
  graphs_astock/rolling_causal_graphs.pkl
  格式：dict[window_end_date_str → np.ndarray shape(N, N)]

运行：
  cd D:\\ICSFP\\HCSF
  D:\\conda\\envs\\ic_sfp_gpu\\python.exe compute_rolling_causal_graph.py
  # 可选参数:
  python compute_rolling_causal_graph.py --window 90 --step 30
"""

import argparse
import logging
import os
import pickle
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import grangercausalitytests
from tqdm import tqdm

# ─── 路径设置 ───────────────────────────────────────────────────
ROOT     = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

OUT_DIR    = ROOT / 'graphs_astock'
OUT_DIR.mkdir(exist_ok=True)

# ─── 参数 ────────────────────────────────────────────────────────
TRAIN_START = '2020-01-02'
TRAIN_END   = '2024-04-08'
MAX_LAGS    = 5
SIG_LEVEL   = 0.05
MIN_OBS     = MAX_LAGS * 4 + 10   # 窗口内最少有效样本数

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s  %(levelname)-7s  %(message)s',
                    datefmt='%H:%M:%S')
logger = logging.getLogger(__name__)


# ====================================================================
# 数据加载
# ====================================================================

def load_all_returns(price_dir: Path) -> tuple[pd.DataFrame, list[str]]:
    """
    读取所有股票 CSV，计算日收益率，拼成 DataFrame。
    返回 (returns_df[日期×股票], stock_codes)。
    支持大小写列名：date/Date, close/Close。
    """
    logger.info(f'从 {price_dir} 加载价格数据…')
    frames = {}
    for csv in sorted(price_dir.glob('*.csv')):
        code = csv.stem
        try:
            raw = pd.read_csv(csv)
            # 统一列名小写，方便查找
            col_map = {c: c.lower() for c in raw.columns}
            raw = raw.rename(columns=col_map)
            # 找日期列
            date_col = next((c for c in raw.columns if c in ('date', 'trade_date', 'datetime')), None)
            if date_col is None:
                continue
            raw[date_col] = pd.to_datetime(raw[date_col].astype(str), infer_datetime_format=True)
            raw = raw.set_index(date_col)
            df = raw
            # 找到 close/收盘 列
            close_col = next((c for c in df.columns
                              if c.lower() in ('close', '收盘', 'close_price')), None)
            if close_col is None:
                continue
            df = df[[close_col]].rename(columns={close_col: code})
            df = df[~df.index.duplicated(keep='last')].sort_index()
            frames[code] = df
        except Exception:
            pass

    if not frames:
        raise RuntimeError(f'未读取到任何价格文件，请检查 {PRICE_DIR}')

    prices = pd.concat(frames.values(), axis=1)
    prices = prices.sort_index()
    prices = prices[prices.index >= TRAIN_START]
    prices = prices[prices.index <= TRAIN_END]

    returns = prices.pct_change().replace([np.inf, -np.inf], np.nan)
    returns = returns.dropna(how='all')

    stock_codes = list(prices.columns)
    logger.info(f'加载完成：{len(stock_codes)} 只股票，{len(returns)} 个交易日')
    # 如果有 stock_codes.txt，按其顺序排列（保证与其他模块一致）
    codes_txt = ROOT / 'graphs_astock' / 'stock_codes.txt'
    if codes_txt.exists():
        ordered = [c for c in codes_txt.read_text().split() if c in prices.columns]
        if ordered:
            prices = prices[ordered]
            returns = returns[ordered]
            stock_codes = ordered
            logger.info(f'按 stock_codes.txt 排序：{len(ordered)} 只')
    return returns, stock_codes


# ====================================================================
# 单窗口因果图计算
# ====================================================================

def _granger_pvalue(x: np.ndarray, y: np.ndarray, max_lags: int) -> float:
    """
    计算 x → y 的 Granger 显著性（最小 p 值跨所有 lag）。
    返回 min p_value（越小代表因果越强）。
    出错则返回 1.0（无显著因果）。
    """
    data = np.column_stack([y, x])          # statsmodels: data[:, 0] 是被解释变量
    if np.std(x) < 1e-10 or np.std(y) < 1e-10:
        return 1.0
    try:
        res = grangercausalitytests(data, maxlag=max_lags, verbose=False)
        pvals = [res[k][0]['ssr_ftest'][1] for k in range(1, max_lags + 1)]
        return float(min(pvals))
    except Exception:
        return 1.0


def compute_window_graph(
    window_returns: pd.DataFrame,
    stock_codes: list[str],
) -> np.ndarray:
    """
    对给定时间窗口的收益率矩阵计算 Granger 因果图。
    返回行归一化的 (N, N) 权重矩阵。
    """
    N = len(stock_codes)
    p_matrix = np.ones((N, N), dtype=np.float32)

    # 仅使用窗口内无 NaN 的股票对
    arr = window_returns.values.astype(np.float64)

    for i in range(N):
        for j in range(N):
            if i == j:
                continue
            xi = arr[:, j]          # j 影响 i
            yi = arr[:, i]
            mask = ~(np.isnan(xi) | np.isnan(yi))
            if mask.sum() < MIN_OBS:
                continue
            p_matrix[i, j] = _granger_pvalue(xi[mask], yi[mask], MAX_LAGS)

    # 权重 = (1 - p_value) 且 p < SIG_LEVEL，否则为 0
    weight = np.where(p_matrix < SIG_LEVEL, 1.0 - p_matrix, 0.0)
    np.fill_diagonal(weight, 0.0)

    # 行归一化
    row_sum = weight.sum(axis=1, keepdims=True)
    row_sum[row_sum == 0] = 1.0
    weight = weight / row_sum

    return weight.astype(np.float32)


# ====================================================================
# 主循环
# ====================================================================

def build_rolling_graphs(window_days: int = 90, step_days: int = 30,
                         price_dir: Path = None) -> dict:
    """
    按滚动窗口计算所有因果图，返回 {window_end_date_str: graph_array}。
    """
    if price_dir is None:
        price_dir = ROOT / 'data' / 'prices_200'
    returns_df, stock_codes = load_all_returns(price_dir)
    dates_all = returns_df.index.to_list()

    start_dt = datetime.strptime(TRAIN_START, '%Y-%m-%d')
    end_dt   = datetime.strptime(TRAIN_END,   '%Y-%m-%d')

    rolling_graphs = {}
    window_start   = start_dt

    logger.info(f'开始计算滚动因果图（window={window_days}d, step={step_days}d）…')
    step_td   = timedelta(days=step_days)
    window_td = timedelta(days=window_days)

    pbar = tqdm(desc='滚动窗口', unit='window')
    while window_start + window_td <= end_dt + timedelta(days=1):
        window_end = window_start + window_td

        # 筛选窗口内的交易日
        mask = (returns_df.index >= window_start) & (returns_df.index < window_end)
        window_df = returns_df.loc[mask]

        if len(window_df) >= MIN_OBS:
            graph = compute_window_graph(window_df, stock_codes)
            key   = window_end.strftime('%Y-%m-%d')
            rolling_graphs[key] = graph
            n_edges = int((graph > 0).sum())
            pbar.set_postfix({'end': key, 'edges': n_edges})
            pbar.update(1)

        window_start += step_td

    pbar.close()
    logger.info(f'共计算 {len(rolling_graphs)} 个窗口的因果图')
    return rolling_graphs, stock_codes


def main():
    parser = argparse.ArgumentParser(description='滚动窗口 Granger 因果图计算')
    parser.add_argument('--window',    type=int, default=180, help='窗口大小（日历天，默认180=半年）')
    parser.add_argument('--step',      type=int, default=90,  help='滑动步长（日历天，默认90=季度）')
    parser.add_argument('--force',     action='store_true',    help='强制重新计算（忽略已有文件）')
    parser.add_argument('--price-dir', type=str, default='',   help='价格 CSV 目录（默认 data/prices_200）')
    args = parser.parse_args()

    price_dir = Path(args.price_dir) if args.price_dir else ROOT / 'data' / 'prices_200'
    if not price_dir.is_dir():
        logger.error(f'价格目录不存在: {price_dir}')
        sys.exit(1)

    # 根据 price_dir 生成输出文件名（区分 62 vs 200 等）
    n_stocks = len(list(price_dir.glob('*.csv')))
    OUT_PATH = OUT_DIR / f'rolling_causal_graphs_{n_stocks}.pkl'
    logger.info(f'价格目录: {price_dir} ({n_stocks} 只股票)')
    logger.info(f'输出文件: {OUT_PATH}')

    if OUT_PATH.exists() and not args.force:
        logger.info(f'已存在: {OUT_PATH}，跳过（加 --force 重新计算）')
        # 展示摘要
        with open(OUT_PATH, 'rb') as f:
            data = pickle.load(f)
        graphs = data.get('graphs', data)
        codes  = data.get('stock_codes', [])
        logger.info(f'  窗口数: {len(graphs)}，股票数: {len(codes)}')
        keys = sorted(graphs.keys())
        logger.info(f'  首尾窗口: {keys[0]} ~ {keys[-1]}')
        return

    rolling_graphs, stock_codes = build_rolling_graphs(args.window, args.step, price_dir)

    # 保存
    save_data = {
        'graphs':      rolling_graphs,   # dict[date_str → ndarray(N,N)]
        'stock_codes': stock_codes,
        'window_days': args.window,
        'step_days':   args.step,
        'computed_at': datetime.now().isoformat(),
    }
    with open(OUT_PATH, 'wb') as f:
        pickle.dump(save_data, f, protocol=4)
    logger.info(f'✅ 保存完成: {OUT_PATH}')
    logger.info(f'   共 {len(rolling_graphs)} 个窗口，每图形状: '
                f'{next(iter(rolling_graphs.values())).shape}')


if __name__ == '__main__':
    main()
