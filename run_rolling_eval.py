#!/usr/bin/env python3
"""
P1: 年度滚动评估脚本 (run_rolling_eval.py)
==========================================
针对 3 个隔离测试年（2022 / 2023 / 2024），
在 3 种情感配置（none / lexicon / roberta）下分别训练并测试，
输出汇总表和 JSON 结果，供论文 Table 使用。

用法:
  cd D:\\ICSFP\\HCSF
  conda activate ic_sfp_gpu

  # 运行全部 9 组实验（顺序执行，每组约 8-12 h）
  python run_rolling_eval.py

  # 只运行指定年份 / 配置（调试用）
  python run_rolling_eval.py --years 2022 --configs roberta

  # 跳过已完成的实验（根据 checkpoint 存在判断）
  python run_rolling_eval.py --skip_done

  # 只汇总已有结果（不重新训练）
  python run_rolling_eval.py --summary_only

输出文件:
  rolling_results/results.json     — 原始结果字典
  rolling_results/summary.txt      — 人类可读汇总表
"""

import argparse
import copy
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import yaml

# ─────────────────────────────────────────────────────────────────
# 常量
# ─────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_CONFIG = SCRIPT_DIR / 'config_astock.yml'
RESULTS_DIR = SCRIPT_DIR / 'rolling_results'
PYTHON_EXE  = sys.executable          # 使用当前 conda 环境的 python

# 三个测试年的日期分割
# 每年：留最后约 3 个月做验证，整年做测试，之前全做训练
YEAR_SPLITS = {
    '2022': {
        'train_start_date': '2020-01-02',
        'train_end_date':   '2021-09-30',
        'dev_start_date':   '2021-10-01',
        'dev_end_date':     '2021-12-31',
        'test_start_date':  '2022-01-01',
        'test_end_date':    '2022-12-31',
    },
    '2023': {
        'train_start_date': '2020-01-02',
        'train_end_date':   '2022-09-30',
        'dev_start_date':   '2022-10-01',
        'dev_end_date':     '2022-12-31',
        'test_start_date':  '2023-01-01',
        'test_end_date':    '2023-12-31',
    },
    '2024': {
        # 原始实验的日期——保持一致
        'train_start_date': '2020-01-02',
        'train_end_date':   '2024-04-08',
        'dev_start_date':   '2024-04-09',
        'dev_end_date':     '2024-11-15',
        'test_start_date':  '2024-11-18',
        'test_end_date':    '2025-01-02',
    },
}

# 情感配置 -> Main_sentiment.py 参数
CONFIGS = {
    'none':     ['--sentiment_type', 'none',    '--no_rolling'],
    'lexicon':  ['--sentiment_type', 'lexicon', '--no_rolling'],
    'roberta':  ['--sentiment_type', 'roberta', '--no_rolling'],
    # P6: 因果图消融（同模型同情感=RoBERTa）
    'graph_granger': ['--sentiment_type', 'roberta', '--causal_method', 'granger', '--no_rolling'],
    'graph_random':  ['--sentiment_type', 'roberta', '--causal_method', 'random',  '--no_rolling'],
    'graph_nograph': ['--sentiment_type', 'roberta', '--causal_method', 'none',    '--no_rolling'],
    # P2: StockNet-CN baseline — 无情感、无因果图（仅 GloVe 文本 + 价格）
    'stocknet': ['--sentiment_type', 'none', '--causal_method', 'none', '--no_rolling'],
}

# ─────────────────────────────────────────────────────────────────
# 辅助函数
# ─────────────────────────────────────────────────────────────────

def make_temp_config(year: str) -> Path:
    """基于 config_astock.yml 生成指定年份的临时配置文件，返回路径。"""
    with open(BASE_CONFIG, 'r', encoding='utf-8') as f:
        cfg = yaml.safe_load(f)

    # 覆盖 dates 节
    cfg['dates'] = YEAR_SPLITS[year]
    # 覆盖 data.date_range（部分代码可能也读这里）
    if 'data' in cfg and 'date_range' in cfg.get('data', {}):
        dr = cfg['data']['date_range']
        splits = YEAR_SPLITS[year]
        dr['train_start'] = splits['train_start_date']
        dr['train_end']   = splits['train_end_date']
        dr['dev_start']   = splits['dev_start_date']
        dr['dev_end']     = splits['dev_end_date']
        dr['test_start']  = splits['test_start_date']
        dr['test_end']    = splits['test_end_date']

    tmp_path = SCRIPT_DIR / f'_rolling_config_{year}.yml'
    with open(tmp_path, 'w', encoding='utf-8') as f:
        yaml.dump(cfg, f, allow_unicode=True, default_flow_style=False)
    return tmp_path


def exp_tag(year: str, config: str) -> str:
    """生成唯一实验标签，如 roll2022_roberta。"""
    return f'roll{year}_{config}'


def checkpoint_exists(year: str, config: str) -> bool:
    """检查实验的 best_model.pth 是否已存在（判断是否已完成）。"""
    tag = exp_tag(year, config)
    # ExecutorSentiment 将 checkpoint 存到 checkpoints_astock/<name>-sent-<tag>/
    for pattern in [
        SCRIPT_DIR / f'checkpoints_astock' / f'*-sent-{tag}' / 'best_model.pth',
        SCRIPT_DIR / f'checkpoints_astock' / f'*{tag}*' / 'best_model.pth',
    ]:
        matches = list(SCRIPT_DIR.glob(str(pattern.relative_to(SCRIPT_DIR))))
        if matches:
            return True
    return False


def parse_test_metrics(log_text: str) -> dict:
    """
    从训练日志输出中解析最后一次测试集指标。
    日志格式（由 stat_logger.print_eval_res）:
      ... Eval, loss: X.X, acc: X.X, mcc: X.X, precision: X.X, recall: X.X, f1: X.X, ...
    返回 {'acc': float, 'mcc': float, 'f1': float, 'precision': float, 'recall': float}
    """
    # 用 kv 方式逐行解析，避免可选 group 被非贪婪 .*? 跳过
    eval_pat = re.compile(r'Eval.*?acc:.*?mcc:')
    kv_pat   = re.compile(r'(\w+):\s*([\-\d.eE+]+)')
    results = []
    for line in log_text.splitlines():
        if not eval_pat.search(line):
            continue
        kvs = dict(kv_pat.findall(line))
        try:
            results.append({
                'acc':       float(kvs['acc']),
                'mcc':       float(kvs['mcc']),
                'precision': float(kvs['precision']) if 'precision' in kvs else None,
                'recall':    float(kvs['recall'])    if 'recall'    in kvs else None,
                'f1':        float(kvs['f1'])        if 'f1'        in kvs else None,
            })
        except (KeyError, ValueError):
            pass
    # 只取最后一次（restore_and_test 的结果）
    return results[-1] if results else {}


def run_one_experiment(year: str, config: str, skip_done: bool = False) -> dict:
    """
    运行单个 (year, config) 组合：生成临时 config → 调用 Main_sentiment.py → 解析结果。
    返回结果 dict。
    """
    tag = exp_tag(year, config)
    print(f'\n{"="*70}')
    print(f'[P1] 实验: year={year}, config={config}, tag={tag}')
    print(f'{"="*70}')

    if skip_done and checkpoint_exists(year, config):
        print(f'  ⏭  已有 checkpoint，跳过训练，仅读取测试结果...')
        return run_test_only(year, config)

    # 生成临时 yaml
    tmp_cfg = make_temp_config(year)
    print(f'  临时配置: {tmp_cfg}')
    print(f'  日期: train={YEAR_SPLITS[year]["train_start_date"]}~{YEAR_SPLITS[year]["train_end_date"]}'
          f'  dev={YEAR_SPLITS[year]["dev_start_date"]}~{YEAR_SPLITS[year]["dev_end_date"]}'
          f'  test={YEAR_SPLITS[year]["test_start_date"]}~{YEAR_SPLITS[year]["test_end_date"]}')

    cmd = [
        PYTHON_EXE, str(SCRIPT_DIR / 'Main_sentiment.py'),
        '--mode', 'train_test',
        '--exp_tag', tag,
    ] + CONFIGS[config]

    env = os.environ.copy()
    env['HCSF_CONFIG'] = str(tmp_cfg)

    print(f'  命令: {" ".join(cmd)}')
    start_time = datetime.now()

    log_lines = []
    try:
        proc = subprocess.Popen(
            cmd,
            cwd=str(SCRIPT_DIR),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        # 实时打印 + 收集
        for line in proc.stdout:
            print(f'    {line}', end='')
            log_lines.append(line)
        proc.wait()
        returncode = proc.returncode
    except Exception as e:
        print(f'  ❌ 子进程异常: {e}')
        return {'year': year, 'config': config, 'error': str(e)}
    finally:
        # 删除临时配置
        try:
            tmp_cfg.unlink()
        except Exception:
            pass

    elapsed = (datetime.now() - start_time).total_seconds() / 3600
    log_text = ''.join(log_lines)

    metrics = parse_test_metrics(log_text)
    result = {
        'year':       year,
        'config':     config,
        'tag':        tag,
        'returncode': returncode,
        'elapsed_h':  round(elapsed, 2),
        **metrics,
    }

    def _fmt(v):
        return f'{v:.3f}' if v is not None else 'N/A'

    if not metrics:
        print(f'  ⚠️  未能从日志解析到测试指标（returncode={returncode}）')
        result['error'] = '未解析到 Eval 行'
    else:
        print(f'  ✅ Test Acc={_fmt(metrics.get("acc"))}  '
              f'MCC={_fmt(metrics.get("mcc"))}  '
              f'F1={_fmt(metrics.get("f1"))}  '
              f'（耗时 {elapsed:.1f}h）')

    return result


def run_test_only(year: str, config: str) -> dict:
    """仅对已存在的 checkpoint 运行 test（跳过训练）。"""
    tag = exp_tag(year, config)
    tmp_cfg = make_temp_config(year)

    cmd = [
        PYTHON_EXE, str(SCRIPT_DIR / 'Main_sentiment.py'),
        '--mode', 'test',
        '--exp_tag', tag,
    ] + CONFIGS[config]

    env = os.environ.copy()
    env['HCSF_CONFIG'] = str(tmp_cfg)

    log_lines = []
    try:
        proc = subprocess.Popen(
            cmd, cwd=str(SCRIPT_DIR), env=env,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1,
        )
        for line in proc.stdout:
            print(f'    {line}', end='')
            log_lines.append(line)
        proc.wait()
        returncode = proc.returncode
    except Exception as e:
        return {'year': year, 'config': config, 'error': str(e)}
    finally:
        try:
            tmp_cfg.unlink()
        except Exception:
            pass

    log_text = ''.join(log_lines)
    metrics  = parse_test_metrics(log_text)
    result   = {'year': year, 'config': config, 'tag': tag,
                'returncode': returncode, **metrics}
    return result


def print_summary(all_results: list) -> str:
    """生成汇总表字符串，同时打印到终端。"""
    lines = []
    lines.append('')
    lines.append('=' * 78)
    lines.append('P1 年度滚动评估汇总 — HCSF 三年均值 ± 标准差')
    lines.append('=' * 78)
    lines.append(f'{"Config":<12} {"Year":<6} {"Acc":>7} {"MCC":>8} {"F1":>7}  Status')
    lines.append('-' * 78)

    # 按 config、year 排序输出
    grouped = {}
    for r in all_results:
        key = r['config']
        grouped.setdefault(key, []).append(r)

    import numpy as np
    summary_rows = {}
    preferred_order = [
        'none', 'stocknet', 'lexicon', 'roberta',
        'graph_granger', 'graph_random', 'graph_nograph'
    ]
    ordered_configs = [c for c in preferred_order if c in grouped] + [
        c for c in sorted(grouped.keys()) if c not in preferred_order
    ]

    for config in ordered_configs:
        rows = grouped.get(config, [])
        for r in sorted(rows, key=lambda x: x['year']):
            acc = r.get('acc')
            mcc = r.get('mcc')
            f1  = r.get('f1')
            status = '✅' if acc is not None else f'❌ {r.get("error","?")}'
            acc_s = f'{acc:.3f}' if acc is not None else '---'
            mcc_s = f'{mcc:.3f}' if mcc is not None else '---'
            f1_s  = f'{f1:.3f}'  if f1  is not None else '---'
            lines.append(f'{config:<12} {r["year"]:<6} {acc_s:>7} {mcc_s:>8} {f1_s:>7}  {status}')

        # 均值 ± std
        accs = [r['acc'] for r in rows if r.get('acc') is not None]
        mccs = [r['mcc'] for r in rows if r.get('mcc') is not None]
        f1s  = [r['f1']  for r in rows if r.get('f1')  is not None]
        if accs:
            acc_m, acc_s = float(np.mean(accs)), float(np.std(accs))
            mcc_m, mcc_s2 = float(np.mean(mccs)), float(np.std(mccs))
            f1_m, f1_s2 = float(np.mean(f1s)), float(np.std(f1s))
            lines.append(f'  {"→ Mean":<10} {"all":<6} '
                         f'{acc_m:.3f}±{acc_s:.3f} '
                         f'{mcc_m:.3f}±{mcc_s2:.3f} '
                         f'{f1_m:.3f}±{f1_s2:.3f}')
            summary_rows[config] = {
                'acc_mean': acc_m, 'acc_std': acc_s,
                'mcc_mean': mcc_m, 'mcc_std': mcc_s2,
                'f1_mean':  f1_m,  'f1_std':  f1_s2,
            }
        lines.append('')

    lines.append('=' * 78)
    lines.append('【论文 Table 格式】（Mean ± Std）')
    lines.append('-' * 78)
    lines.append(f'{"Config":<14} {"Acc (%)":<18} {"MCC":<18} {"Macro-F1":<18}')
    lines.append('-' * 78)
    for config in ordered_configs:
        if config in summary_rows:
            r = summary_rows[config]
            lines.append(
                f'{config:<14} '
                f'{r["acc_mean"]*100:.1f}±{r["acc_std"]*100:.1f}{"":>6} '
                f'{r["mcc_mean"]:.3f}±{r["mcc_std"]:.3f}{"":>6} '
                f'{r["f1_mean"]:.3f}±{r["f1_std"]:.3f}'
            )
    lines.append('=' * 78)

    text = '\n'.join(lines)
    print(text)
    return text


# ─────────────────────────────────────────────────────────────────
# 主函数
# ─────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(description='P1 年度滚动评估')
    p.add_argument('--years',   nargs='+', default=['2022', '2023', '2024'],
                   choices=['2022', '2023', '2024'],
                   help='要评估的测试年份（默认全部）')
    p.add_argument('--configs', nargs='+', default=['none', 'lexicon', 'roberta'],
                   choices=['none', 'lexicon', 'roberta', 'stocknet',
                            'graph_granger', 'graph_random', 'graph_nograph'],
                   help='要评估的情感配置（默认全部；stocknet=P2 baseline）')
    p.add_argument('--skip_done',    action='store_true',
                   help='跳过已有 best_model.pth 的实验，只运行未完成的')
    p.add_argument('--summary_only', action='store_true',
                   help='仅读取已有 results.json 并打印汇总，不训练')
    p.add_argument('--dry_run',      action='store_true',
                   help='仅打印实验计划，不实际运行')
    return p.parse_args()


def main():
    args = parse_args()

    RESULTS_DIR.mkdir(exist_ok=True)
    results_json = RESULTS_DIR / 'results.json'
    summary_txt  = RESULTS_DIR / 'summary.txt'

    # 加载已有结果
    all_results = []
    if results_json.exists():
        with open(results_json, 'r', encoding='utf-8') as f:
            all_results = json.load(f)
        print(f'[INFO] 已加载 {len(all_results)} 条历史结果 from {results_json}')

    if args.summary_only:
        summary = print_summary(all_results)
        with open(summary_txt, 'w', encoding='utf-8') as f:
            f.write(summary)
        return

    # 构建实验计划
    plan = [(y, c) for y in args.years for c in args.configs]
    print(f'[P1] 实验计划：{len(plan)} 个组合')
    for i, (y, c) in enumerate(plan, 1):
        done = checkpoint_exists(y, c)
        skip = args.skip_done and done
        print(f'  {i:2d}. year={y}, config={c}, tag={exp_tag(y, c)}'
              f'{"  [已完成，将跳过]" if skip else "  [已有ckpt，重用]" if done else ""}')

    if args.dry_run:
        print('\n[dry_run] 不执行实验，退出。')
        return

    print(f'\n预计总耗时：{len(plan) * 8}～{len(plan) * 12} 小时（每组 8-12h，顺序执行）')
    print('开始时间：', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    # 去重（避免重复记录同一组）
    seen = {(r['year'], r['config']) for r in all_results}

    for year, config in plan:
        result = run_one_experiment(year, config, skip_done=args.skip_done)

        # 更新结果列表（覆盖同 key 的旧结果）
        all_results = [r for r in all_results
                       if not (r['year'] == year and r['config'] == config)]
        all_results.append(result)

        # 实时保存（防断电丢失）
        with open(results_json, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        print(f'  → 结果已保存: {results_json}')

    # 最终汇总
    summary = print_summary(all_results)
    with open(summary_txt, 'w', encoding='utf-8') as f:
        f.write(summary)
    print(f'\n[完成] 汇总已保存: {summary_txt}')
    print(f'[完成] 原始结果: {results_json}')
    print('结束时间：', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))


if __name__ == '__main__':
    main()
