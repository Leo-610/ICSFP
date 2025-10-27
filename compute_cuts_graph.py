#!/usr/bin/env python3
import os
import numpy as np
import torch
from typing import List
from ConfigLoader import path_parser, dates, stock_symbols, logger


def load_close_matrix(symbols: List[str], start_date: str, end_date: str):
    import datetime as dt
    from datetime import datetime
    # Build date index from price files; we will align by scanning all files and taking intersection
    series = {}
    date_set = None
    for s in symbols:
        fp = os.path.join(path_parser.movement, f"{s}.txt")
        if not os.path.exists(fp):
            logger.warning(f"Price file missing for {s}: {fp}")
            continue
        ds = []
        with open(fp, 'r', encoding='utf-8') as f:
            for line in f:
                cols = line.strip().split('\t')
                if len(cols) < 6:
                    continue
                d = cols[0]
                # filter by range
                if not (start_date <= d < end_date):
                    continue
                close = float(cols[5])
                ds.append((d, close))
        ds = sorted(ds, key=lambda x: x[0])
        series[s] = ds
        days = set([d for d,_ in ds])
        date_set = days if date_set is None else (date_set & days)

    if not series or not date_set:
        raise RuntimeError('No overlapping dates across symbols. Check price files and date ranges.')

    dates_sorted = sorted(list(date_set))
    T = len(dates_sorted)
    S = len(symbols)
    X = np.zeros((T, S), dtype=np.float32)
    for j, s in enumerate(symbols):
        ds_map = dict(series.get(s, []))
        for i, d in enumerate(dates_sorted):
            X[i, j] = ds_map.get(d, np.nan)
    # drop rows with nan
    mask = ~np.isnan(X).any(axis=1)
    X = X[mask]
    return X


def build_graph_cuts(X: np.ndarray) -> np.ndarray:
    from multiscale_views import build_multiscale_views
    import cuts_plus
    try:
        from omegaconf import OmegaConf
        # try opt file under CUTS_Plus or repo root
        cand = [os.path.join('opt','lorenz_example.yaml'), os.path.join('CUTS_Plus','opt','lorenz_example.yaml')]
        opt_path = next((p for p in cand if os.path.exists(p)), None)
        opt = OmegaConf.load(opt_path) if opt_path else None
    except Exception:
        opt = None

    # compute returns along time
    # views
    out = build_multiscale_views(X, top_k=3, preproc='log_return', standardize=True, post_standardize=True)
    views = out['views']
    graphs = []
    mask = np.ones_like(X, dtype=bool)
    for _, Xs in views.items():
        try:
            if opt is not None:
                g = cuts_plus.main(Xs, mask, None, opt, None, device='cpu')
            else:
                g = cuts_plus.main(None)
        except TypeError:
            g = cuts_plus.main(None)
        g = np.asarray(g)
        if g.ndim == 2 and g.shape[0] == g.shape[1] == X.shape[1]:
            graphs.append(g)
    if not graphs:
        logger.warning('CUTS+ failed; fallback to abs-corr graph.')
        R = np.corrcoef(np.diff(X,axis=0).T)
        R = np.nan_to_num(np.abs(R))
        np.fill_diagonal(R, 0.0)
        rs = R.sum(axis=1, keepdims=True)
        rs[rs==0]=1.0
        return (R/rs).astype(np.float32)
    G = np.mean(graphs, axis=0).astype(np.float32)
    # row-normalize abs
    A = np.abs(G)
    rs = A.sum(axis=1, keepdims=True)
    rs[rs==0]=1.0
    return (A/rs).astype(np.float32)


def main():
    # build on train period
    start = dates['train_start_date']
    end = dates['dev_start_date']
    syms = stock_symbols
    logger.info(f'Building CUTS+ graph on {len(syms)} symbols: {start} -> {end}')
    X = load_close_matrix(syms, start, end)
    G = build_graph_cuts(X)
    np.save('causal_graph.npy', G)
    logger.info(f'Saved causal graph to causal_graph.npy with shape {G.shape}')


if __name__ == '__main__':
    main()

