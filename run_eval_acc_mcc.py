#!/usr/bin/env python3
import os
import sys
import argparse
import numpy as np
import torch

from ConfigLoader import logger
from Model import Model
from DataPipe import DataPipe
import metrics as metrics


def load_or_make_causal_graph(n_stocks: int, path: str = 'causal_graph.npy') -> np.ndarray:
    """Load saved causal graph or generate a sparse random one for testing."""
    if os.path.exists(path):
        g = np.load(path)
        logger.info(f'Loaded causal graph from {path} with shape {g.shape}')
        return g

    # Fallback: make a sparse row-normalized random matrix
    rng = np.random.RandomState(42)
    g = rng.rand(n_stocks, n_stocks)
    threshold = 0.8  # keep ~20%
    g = np.where(g > threshold, g, 0.0)
    np.fill_diagonal(g, 0.0)
    row_sums = g.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1.0
    g = g / row_sums
    np.save(path, g)
    logger.info(f'Generated random causal graph with shape {g.shape}, saved to {path}')
    return g


def to_device(batch_dict, device):
    out = {}
    for k, v in batch_dict.items():
        if isinstance(v, np.ndarray):
            out[k] = torch.from_numpy(v).to(device)
        else:
            out[k] = v
    return out


def _strip_causal_suffix(path: str) -> str:
    base = path
    for suf in ("_nocausal", "_causal"):
        if base.endswith(suf):
            base = base[: -len(suf)]
            break
    return base


def evaluate_test(device: str = None, use_causal: bool = False):
    device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
    logger.info(f'Using device: {device}')

    # Data and model
    pipe = DataPipe()
    # Build a causal graph aligned with number of stocks encountered during batching
    # We will lazily set the model once we see first batch to get stock count
    model = None

    gen_loss_list = []
    gen_size, gen_n_acc = 0.0, 0.0
    y_list, y_list_ = [], []

    with torch.no_grad():
        for gen_batch in pipe.batch_gen_by_stocks('test'):
            # Lazily construct model when first batch arrives to infer B
            if model is None:
                batch_size = int(gen_batch['batch_size'])
                # Build model with or without causal graph
                if use_causal:
                    g_np = load_or_make_causal_graph(n_stocks=batch_size)
                    g_t = torch.tensor(g_np, dtype=torch.float32)
                    model = Model(graph=g_t)
                else:
                    model = Model(graph=None)
                model.to(device)
                # Init word embeddings
                word_table_init = pipe.init_word_table()
                model.init_word_table(word_table_init)
                model.eval()

                # Try restore checkpoint with fallback to legacy dir
                tried = []
                for try_dir in (model.tf_checkpoints_path, _strip_causal_suffix(model.tf_checkpoints_path)):
                    ckpt_path = os.path.join(try_dir, 'model.pth')
                    tried.append(ckpt_path)
                    if os.path.exists(ckpt_path):
                        try:
                            ckpt = torch.load(ckpt_path, map_location=device)
                            model.load_state_dict(ckpt['model_state_dict'], strict=False)
                            logger.info(f'Restored checkpoint: {ckpt_path}')
                            break
                        except Exception as e:
                            logger.warning(f'Failed to restore checkpoint {ckpt_path}: {e}')

            batch = to_device(gen_batch, device)

            outputs = model(
                word_ph=batch['word_batch'],
                price_ph=batch['price_batch'],
                stock_ph=batch['stock_batch'],
                T_ph=batch['T_batch'],
                n_words_ph=batch['n_words_batch'],
                n_msgs_ph=batch['n_msgs_batch'],
                y_ph=batch['y_batch'],
                ss_index_ph=batch['ss_index_batch'],
                is_training=False,
            )

            # Loss for logging only
            loss = model.compute_loss(outputs, batch['T_batch'])
            gen_loss_list.append(loss.item())

            # Collect predictions and labels
            y = outputs['y_T'].detach().cpu().numpy()
            y_ = outputs['y_T_'].detach().cpu().numpy()
            y_list.append(y)
            y_list_.append(y_)

            # Accumulate accuracy counts
            gen_batch_n_acc = float(metrics.n_accurate_numpy(y, y_))
            gen_n_acc += gen_batch_n_acc
            gen_size += float(batch['batch_size'])

    # Final metrics with MCC
    res = metrics.eval_res(
        gen_n_acc=gen_n_acc,
        gen_size=gen_size,
        gen_loss_list=gen_loss_list,
        y_list=y_list,
        y_list_=y_list_,
        use_mcc=True,
    )

    acc = res.get('acc', 0.0)
    mcc = res.get('mcc', None)
    logger.info(f'Test ACC: {acc:.4f}')
    if mcc is None:
        logger.info('Test MCC: None (insufficient positive/negative samples)')
    else:
        logger.info(f'Test MCC: {mcc:.4f}')

    # Also print to stdout for quick capture
    print(f'ACC: {acc:.6f}')
    print(f'MCC: {"None" if mcc is None else f"{mcc:.6f}"}')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--causal', type=int, default=0, help='1 to enable causal graph, 0 to disable')
    args = ap.parse_args()

    # Reproducibility
    torch.manual_seed(42)
    np.random.seed(42)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(42)

    try:
        evaluate_test(use_causal=bool(args.causal))
    except Exception as e:
        # Surface error succinctly to user and exit non-zero
        logger.error(f'run_eval_acc_mcc failed: {e}')
        raise
