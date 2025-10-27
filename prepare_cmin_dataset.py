#!/usr/bin/env python3
import os
import argparse
import pandas as pd
import numpy as np
import yaml


def make_movement_txt(df: pd.DataFrame, out_dir: str):
    os.makedirs(out_dir, exist_ok=True)
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    dates = df['date'].dt.strftime('%Y-%m-%d').tolist()
    symbols = [c for c in df.columns if c != 'date']
    X = df[symbols].values.astype(float)
    # compute movement percent per day: (p_t - p_{t-1})/p_{t-1}
    mv = np.zeros_like(X)
    mv[1:, :] = (X[1:, :] - X[:-1, :]) / (X[:-1, :] + 1e-8)

    for j, sym in enumerate(symbols):
        fp = os.path.join(out_dir, f"{sym}.txt")
        with open(fp, 'w', encoding='utf-8') as f:
            for i, d in enumerate(dates):
                m = mv[i, j]
                price = X[i, j]
                # format: date, mv, placeholder, high, low, close (use close for H/L)
                f.write(f"{d}\t{m:.8f}\t0\t{price:.6f}\t{price:.6f}\t{price:.6f}\n")


def write_config(base_cfg_path: str, out_cfg_path: str, movement_dir: str, symbols: list,
                 train_start: str, dev_start: str, test_start: str, test_end: str):
    with open(base_cfg_path, 'r', encoding='utf-8') as f:
        cfg = yaml.safe_load(f)
    # paths
    cfg['paths']['price'] = movement_dir
    # also set dataset-specific tweet path (user must place tweets here)
    if 'tweet_preprocessed' in cfg['paths']:
        # infer dataset suffix from movement_dir
        # movement_dir like 'price/preprocessed_cmin-cn' -> 'tweet/preprocessed_cmin-cn'
        suffix = movement_dir.split('price/', 1)[-1]
        cfg['paths']['tweet_preprocessed'] = f"tweet/{suffix}"
    # dates
    cfg['dates']['train_start_date'] = train_start
    cfg['dates']['train_end_date'] = dev_start
    cfg['dates']['dev_start_date'] = dev_start
    cfg['dates']['dev_end_date'] = test_start
    cfg['dates']['test_start_date'] = test_start
    cfg['dates']['test_end_date'] = test_end
    # stocks (single group)
    cfg['stocks'] = {'cmin': symbols}

    with open(out_cfg_path, 'w', encoding='utf-8') as f:
        yaml.safe_dump(cfg, f, allow_unicode=True, sort_keys=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dataset', choices=['cmin-cn', 'cmin-us'], required=True)
    args = ap.parse_args()

    csv_map = {
        'cmin-cn': 'data/stocks-cmin-cn_filled.csv',
        'cmin-us': 'data/stocks-cmin-us_filled.csv',
    }
    csv_path = csv_map[args.dataset]
    df = pd.read_csv(csv_path)

    # symbols
    symbols = [c for c in df.columns if c != 'date']

    # movement dir
    movement_dir = f"data/price/preprocessed_{args.dataset}"
    make_movement_txt(df, movement_dir)

    # date splits (70/10/20 by time)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    T = len(df)
    t1 = int(T * 0.7)
    t2 = int(T * 0.8)
    train_start = df['date'].iloc[0].strftime('%Y-%m-%d')
    dev_start = df['date'].iloc[t1].strftime('%Y-%m-%d')
    test_start = df['date'].iloc[t2].strftime('%Y-%m-%d')
    test_end = df['date'].iloc[-1].strftime('%Y-%m-%d')

    # config file
    base_cfg = 'config.yml'
    out_cfg = f"config_{args.dataset}.yml"
    # For config, price path should be relative to data root (under paths.data)
    price_rel = f"price/preprocessed_{args.dataset}"
    write_config(base_cfg, out_cfg, price_rel, symbols, train_start, dev_start, test_start, test_end)

    print(f"Prepared movement files at: {movement_dir}")
    print(f"Wrote config: {out_cfg}")
    print(f"Stocks: {len(symbols)}, Dates: {train_start} -> {test_end}")


if __name__ == '__main__':
    main()
