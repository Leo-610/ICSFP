#!/usr/bin/env python3
import os
import argparse
import math
import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader

from ConfigLoader import logger, config_model
from Model import Model
import metrics as M


class CMINWindowDataset(Dataset):
    def __init__(self, df: pd.DataFrame, stock_cols, window: int, split: str,
                 train_ratio=0.7, dev_ratio=0.1, standardize=True):
        assert split in {"train", "dev", "test"}
        self.window = window
        self.stock_cols = stock_cols

        # sort by date
        df = df.copy()
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)

        # close price matrix [T, S]
        X = df[stock_cols].values.astype(np.float32)

        # compute next-day return label per stock [T, S]
        ret = np.diff(X, axis=0) / (X[:-1] + 1e-6)
        # align to predict day t using history up to t-1
        # valid indices start at t = window to T-2 (since label at t uses ret[t])
        T = X.shape[0]
        # split indices by time
        n_train = int(T * train_ratio)
        n_dev = int(T * dev_ratio)
        bounds = {
            'train': (window, max(window, n_train - 1)),
            'dev': (max(window, n_train), max(window, n_train + n_dev - 1)),
            'test': (max(window, n_train + n_dev), T - 2),
        }
        t0, t1 = bounds[split]

        # optional standardization using train stats only
        if standardize:
            X_train = X[:max(window, n_train)]
            mu = np.nanmean(X_train, axis=0, keepdims=True)
            sigma = np.nanstd(X_train, axis=0, keepdims=True) + 1e-6
            Xn = (X - mu) / sigma
        else:
            Xn = X

        # build samples: each sample is (stock_idx, end_t)
        samples = []
        for t in range(t0, t1 + 1):
            # label at t is ret[t, s] -> up if >0
            for s_idx, _ in enumerate(stock_cols):
                # require non-nan window and label
                if np.any(np.isnan(Xn[t - window + 1:t + 1, s_idx])):
                    continue
                if np.isnan(ret[t, s_idx]):
                    continue
                samples.append((t, s_idx))

        self.Xn = Xn
        self.X = X
        self.ret = ret
        self.samples = samples
        self.window = window

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        t, s = self.samples[idx]
        # price features: replicate close into [high, low, close]
        seq = self.Xn[t - self.window + 1:t + 1, s]
        price = np.stack([seq, seq, seq], axis=-1)  # [W, 3]
        # label: next-day return sign (here use ret[t, s])
        up = 1.0 if self.ret[t, s] > 0.0 else 0.0
        y = np.array([1.0 - up, up], dtype=np.float32)
        return {
            'price': price.astype(np.float32),
            'y': y,
            'stock_idx': np.int32(s),
            'T': np.int32(self.window),
        }


def collate_batch(batch, max_days, max_msgs, max_words, y_size):
    B = len(batch)
    price_ph = np.zeros((B, max_days, 3), dtype=np.float32)
    y_ph = np.zeros((B, max_days, y_size), dtype=np.float32)
    T_ph = np.zeros((B,), dtype=np.int32)
    stock_ph = np.zeros((B,), dtype=np.int64)

    # dummy text tensors
    word_ph = np.zeros((B, max_days, max_msgs, max_words), dtype=np.int64)
    n_words_ph = np.zeros((B, max_days, max_msgs), dtype=np.int64)
    n_msgs_ph = np.zeros((B, max_days), dtype=np.int64)
    ss_index_ph = np.zeros((B, max_days, max_msgs), dtype=np.int64)

    for i, item in enumerate(batch):
        price = item['price']
        T = min(price.shape[0], max_days)
        price_ph[i, :T] = price[-T:]
        y_ph[i, T - 1] = item['y']
        T_ph[i] = T
        stock_ph[i] = item['stock_idx']

    return {
        'price_ph': torch.from_numpy(price_ph),
        'y_ph': torch.from_numpy(y_ph),
        'T_ph': torch.from_numpy(T_ph),
        'stock_ph': torch.from_numpy(stock_ph),
        'word_ph': torch.from_numpy(word_ph),
        'n_words_ph': torch.from_numpy(n_words_ph),
        'n_msgs_ph': torch.from_numpy(n_msgs_ph),
        'ss_index_ph': torch.from_numpy(ss_index_ph),
        'batch_size': B,
    }


def build_static_graph_from_returns(train_df: pd.DataFrame, stock_cols):
    X = train_df[stock_cols].values.astype(np.float32)
    ret = np.diff(X, axis=0) / (X[:-1] + 1e-6)
    C = np.corrcoef(ret.T)
    C = np.nan_to_num(C, nan=0.0)
    np.fill_diagonal(C, 0.0)
    # row-normalize abs correlation
    A = np.abs(C)
    rs = A.sum(axis=1, keepdims=True)
    rs[rs == 0] = 1.0
    A = A / rs
    return A.astype(np.float32)


def run_for_dataset(csv_path: str, use_causal: bool, device: str = None,
                    epochs: int = 3, batch_size: int = 128, lr: float = 1e-3):
    device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
    logger.info(f'Running on {device}; dataset={csv_path}; causal={use_causal}')

    df = pd.read_csv(csv_path)
    stock_cols = [c for c in df.columns if c != 'date']

    W = int(config_model['max_n_days'])
    max_msgs = int(config_model['max_n_msgs'])
    max_words = int(config_model['max_n_words'])
    y_size = int(config_model['y_size'])

    # Datasets
    ds_train = CMINWindowDataset(df, stock_cols, window=W, split='train')
    ds_dev = CMINWindowDataset(df, stock_cols, window=W, split='dev')
    ds_test = CMINWindowDataset(df, stock_cols, window=W, split='test')

    logger.info(f"Train samples={len(ds_train)}, Dev={len(ds_dev)}, Test={len(ds_test)}")

    dl_train = DataLoader(ds_train, batch_size=batch_size, shuffle=True,
                          collate_fn=lambda b: collate_batch(b, W, max_msgs, max_words, y_size))
    dl_dev = DataLoader(ds_dev, batch_size=batch_size, shuffle=False,
                        collate_fn=lambda b: collate_batch(b, W, max_msgs, max_words, y_size))
    dl_test = DataLoader(ds_test, batch_size=batch_size, shuffle=False,
                         collate_fn=lambda b: collate_batch(b, W, max_msgs, max_words, y_size))

    # Build model
    graph = None
    if use_causal:
        # build graph from train period only
        train_df = df.iloc[:int(len(df) * 0.7) + 1]
        graph_np = build_static_graph_from_returns(train_df, stock_cols)
        graph = torch.tensor(graph_np, dtype=torch.float32)

    model = Model(graph=graph, variant_type='tech')
    model.to(device)

    optim = torch.optim.Adam(model.parameters(), lr=lr)

    def eval_loader(dloader):
        model.eval()
        tot, nacc = 0.0, 0.0
        ys, ys_ = [], []
        losses = []
        with torch.no_grad():
            for batch in dloader:
                for k in list(batch.keys()):
                    if isinstance(batch[k], torch.Tensor):
                        batch[k] = batch[k].to(device)
                out = model(
                    word_ph=batch['word_ph'], price_ph=batch['price_ph'], stock_ph=batch['stock_ph'],
                    T_ph=batch['T_ph'], n_words_ph=batch['n_words_ph'], n_msgs_ph=batch['n_msgs_ph'],
                    y_ph=batch['y_ph'], ss_index_ph=batch['ss_index_ph'], is_training=False
                )
                loss = model.compute_loss(out, batch['T_ph'])
                y = out['y_T'].detach().cpu().numpy()
                y_ = out['y_T_'].detach().cpu().numpy()
                ys.append(y)
                ys_.append(y_)
                nacc += float(M.n_accurate_numpy(y, y_))
                tot += float(batch['batch_size'])
                losses.append(loss.item())
        res = M.eval_res(nacc, tot, losses, ys, ys_, use_mcc=True)
        return res

    # quick training
    for ep in range(epochs):
        model.train()
        for batch in dl_train:
            for k in list(batch.keys()):
                if isinstance(batch[k], torch.Tensor):
                    batch[k] = batch[k].to(device)
            optim.zero_grad()
            out = model(
                word_ph=batch['word_ph'], price_ph=batch['price_ph'], stock_ph=batch['stock_ph'],
                T_ph=batch['T_ph'], n_words_ph=batch['n_words_ph'], n_msgs_ph=batch['n_msgs_ph'],
                y_ph=batch['y_ph'], ss_index_ph=batch['ss_index_ph'], is_training=True
            )
            loss = model.compute_loss(out, batch['T_ph'])
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), model.clip)
            optim.step()
        dev = eval_loader(dl_dev)
        logger.info(f"Epoch {ep+1}: Dev acc={dev['acc']:.4f} mcc={dev.get('mcc')} loss={dev['loss']:.4f}")

    test = eval_loader(dl_test)
    logger.info(f"TEST acc={test['acc']:.6f} mcc={test.get('mcc')}")
    print(f"ACC: {test['acc']:.6f}")
    print(f"MCC: {test.get('mcc')}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dataset', choices=['cmin-cn', 'us'], required=True,
                    help='Choose dataset under data/: stocks-cmin-cn_filled.csv or stocks-cmin-us_filled.csv')
    ap.add_argument('--causal', type=int, default=0, help='1 to use static causal graph from returns')
    ap.add_argument('--epochs', type=int, default=3)
    ap.add_argument('--batch-size', type=int, default=128)
    ap.add_argument('--lr', type=float, default=1e-3)
    args = ap.parse_args()

    csv_map = {
        'cmin-cn': 'data/stocks-cmin-cn_filled.csv',
        'us': 'data/stocks-cmin-us_filled.csv',
    }
    run_for_dataset(csv_map[args.dataset], use_causal=bool(args.causal),
                    epochs=args.epochs, batch_size=args.batch_size, lr=args.lr)


if __name__ == '__main__':
    torch.manual_seed(42)
    np.random.seed(42)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(42)
    main()
