

import torch

from Executor import Executor
from Model import Model
from StockPredictionViewer import StockPredictionViewer

torch.autograd.set_detect_anomaly(True)
print("异常检测已启用")


import pandas as pd

# 设置参数
processed_folder = 'data/price/processed'
start_date = '2014-11-20'


# 方法1：从CSV加载（推荐，更直观）
def load_from_csv():
    # 加载CSV文件
    df = pd.read_csv(f'{processed_folder}/aligned_adj_close.csv',
                     index_col=0,
                     parse_dates=True)

    # 筛选2014年11月20日之后的数据
    df_filtered = df[df.index >= start_date]

    # 转换为NumPy数组
    data_array = df_filtered.values

    # 获取股票列表和日期列表（可选，供参考）
    stock_list = df_filtered.columns.tolist()
    date_list = df_filtered.index.tolist()

    return data_array, stock_list, date_list


# 方法2：从NPY加载
def load_from_npy():
    # 加载NumPy数组和元数据
    data_array = np.load(f'{processed_folder}/aligned_adj_close.npy')
    metadata = np.load(f'{processed_folder}/aligned_metadata.npy', allow_pickle=True).item()

    # 将日期字符串转换为datetime对象
    dates = pd.to_datetime(metadata['dates'])

    # 找到起始日期的索引
    start_idx = np.where(dates >= pd.to_datetime(start_date))[0]

    if len(start_idx) == 0:
        print(f"警告：没有找到{start_date}之后的数据")
        return None, None, None

    # 切片获取所需数据
    data_array_filtered = data_array[start_idx[0]:, :]
    stock_list = metadata['stocks']
    date_list = dates[start_idx[0]:].tolist()

    return data_array_filtered, stock_list, date_list


# 主加载函数（推荐使用）
def load_stock_data_after_date(start_date='2014-11-20', method='csv'):
    """
    加载指定日期之后的股票数据

    Parameters:
    start_date: 起始日期，格式 'YYYY-MM-DD'
    method: 'csv' 或 'npy'，选择加载方式

    Returns:
    data: NumPy数组，shape为(时间步, 股票数量)
    stocks: 股票代码列表
    dates: 日期列表
    """
    if method == 'csv':
        data, stocks, dates = load_from_csv()
    else:
        data, stocks, dates = load_from_npy()

    if data is not None:
        print(f"数据加载成功！")
        print(f"- 数据形状: {data.shape}")
        print(f"- 时间范围: {dates[0].strftime('%Y-%m-%d')} 到 {dates[-1].strftime('%Y-%m-%d')}")
        print(f"- 股票数量: {len(stocks)}")
        print(f"- 股票列表: {stocks[:5]}...（显示前5个）")

        # 显示缺失值信息
        nan_count = np.isnan(data).sum()
        total_count = data.size
        print(f"- 缺失值: {nan_count} ({nan_count / total_count * 100:.2f}%)")

    return data, stocks, dates


# ===== 执行加载 =====
# 使用CSV方法加载（推荐）
data, stocks, dates = load_stock_data_after_date(start_date='2014-11-20', method='csv')

# 如果只需要纯NumPy数组，直接使用data变量
print(f"data形状: {data.shape}")

def _np_print(a, name="array"):
    with np.printoptions(precision=4, suppress=True, linewidth=140, threshold=200):
        print(f"{name}: shape={a.shape}, dtype={a.dtype}")
        print(a)


def _to_numpy(x):
    try:
        import torch
        if isinstance(x, torch.Tensor):
            return x.detach().cpu().numpy()
    except Exception:
        pass
    return x


def show_graph(graph, name="graph"):
    """
    尽量把 cuts_plus.main 的返回结构打印清楚：
    - 如果是 ndarray / torch.Tensor：打印形状与内容
    - 如果是 dict：优先打印常见的邻接矩阵键（'adj','A','graph','adjacency'）
    - 其它类型：打印类型与摘要
    """
    print("=" * 100)
    print(f"[{name}] type = {type(graph).__name__}")

    # numpy / torch.Tensor
    if isinstance(graph, np.ndarray):
        _np_print(graph, f"{name}(ndarray)")
        return

    try:
        import torch
        if isinstance(graph, torch.Tensor):
            _np_print(graph.detach().cpu().numpy(), f"{name}(torch)")
            return
    except Exception:
        pass

    # dict: 尝试找邻接矩阵相关键
    if isinstance(graph, dict):
        keys = list(graph.keys())
        print(f"{name} keys:", keys)
        for k in ['adj', 'A', 'graph', 'adjacency', 'edge_index', 'edge_weight']:
            if k in graph:
                val = _to_numpy(graph[k])
                if isinstance(val, np.ndarray):
                    _np_print(val, f"{name}[{k}]")
                else:
                    print(f"{name}[{k}] -> type={type(val).__name__}")
        return

    # list/tuple: 打印长度与前几个元素类型
    if isinstance(graph, (list, tuple)):
        print(f"{name} length={len(graph)}")
        for i, v in enumerate(graph[:5]):
            v_np = _to_numpy(v)
            if isinstance(v_np, np.ndarray):
                _np_print(v_np, f"{name}[{i}]")
            else:
                print(f"{name}[{i}] -> type={type(v).__name__}")
        return

    # 其它：直接打印
    print(graph)

from os.path import join as opj
import numpy as np
from omegaconf import OmegaConf
# 在训练开始前添加
import torch

from datetime import datetime
from matplotlib import pyplot as plt

from utils.misc import reproduc
from utils.logger import MyLogger
from multiscale_views import build_multiscale_views
import cuts_plus

sector_groups = {
    'materials': ['XOM', 'RDS-B', 'PTR', 'CVX', 'TOT', 'BP', 'BHP', 'SNP', 'SLB', 'BBL'],
    'consumer_goods': ['AAPL', 'PG', 'BUD', 'KO', 'PM', 'TM', 'PEP', 'UN', 'UL', 'MO'],
    'healthcare': ['JNJ', 'PFE', 'NVS', 'UNH', 'MRK', 'AMGN', 'MDT', 'ABBV', 'SNY', 'CELG'],
    'services': ['AMZN', 'BABA', 'WMT', 'CMCSA', 'HD', 'DIS', 'MCD', 'CHTR', 'UPS', 'PCLN'],
    'utilities': ['NEE', 'DUK', 'D', 'SO', 'NGG', 'AEP', 'PCG', 'EXC', 'SRE', 'PPL'],
    'cong': ['IEP', 'HRG', 'CODI', 'REX', 'SPLP', 'PICO', 'AGFS', 'GMRE'],
    'finance': ['BCH', 'BSAC', 'BRK-A', 'JPM', 'WFC', 'BAC', 'V', 'C', 'HSBC', 'MA'],
    'industrial_goods': ['GE', 'MMM', 'BA', 'HON', 'UTX', 'LMT', 'CAT', 'GD', 'DHR', 'ABB'],
    'tech': ['GOOG', 'MSFT', 'FB', 'T', 'CHL', 'ORCL', 'TSM', 'VZ', 'INTC', 'CSCO']
}
# 创建配置
config = {
    'dir_name': 'outputs',
    'task_name': 'stock_causal_discovery',

    'log': {
        'stdout': False,
        'stderr': False,
        'tensorboard': True
    },

    'reproduc': {
        'seed': 42,
        'benchmark': False,
        'deterministic': True
    },

    'data': {
        'missing': {
            'p_noise': 0.0,  # 如果数据已经有缺失值，设为0
            'p_block': 0.0,  # 如果不需要额外添加块缺失，设为0
            'max_seq': 48,
            'min_seq': 12
        }
    },

    'sota': {
        'cuts_plus': {
            'n_nodes': 'auto',  # 自动检测节点数（股票数）
            'input_step': 5,  # 使用过去5个时间步来预测，可以调整
            'batch_size': 256,  # 256也没爆，还可以继续增加
            'data_dim': 1,
            'total_epoch': 100,  # 训练轮数，可根据需要调整

            'n_groups': 32,
            'group_policy': 'multiply_2_every_20',

            'supervision_policy': 'masked_before_100',
            'fill_policy': 'rate_0.1_after_20',
            'show_graph_every': 20,  # 每20轮显示一次因果图

            'data_pred': {
                'model': 'multi_lstm',
                'pred_step': 1,  # 预测未来1个时间步
                'mlp_hid': 64,  # 增大隐藏层，处理复杂的股票数据
                'gru_layers': 2,  # 使用2层GRU
                'shared_weights_decoder': False,
                'concat_h': True,
                'lr_data_start': 1e-3,
                'lr_data_end': 1e-4,
                'weight_decay': 1e-5,
                'prob': True
            },

            'graph_discov': {
                'lambda_s_start': 1e-1,
                'lambda_s_end': 1e-2,
                'lr_graph_start': 1e-3,
                'lr_graph_end': 1e-4,
                'start_tau': 1,
                'end_tau': 0.1,
                'dynamic_sampling_milestones': [0],
                'dynamic_sampling_periods': [1]
            },

            'causal_thres': 'value_0.3'  # 因果阈值，可根据结果调整
        }
    }
}

# 转换为OmegaConf对象
opt = OmegaConf.create(config)

# 设置设备
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"使用设备: {device}")

# 设置随机种子
reproduc(**opt.reproduc)

# 创建时间戳和项目路径
timestamp = datetime.now().strftime("_%Y_%m%d_%H%M%S")
opt.task_name += timestamp
proj_path = opj(opt.dir_name, opt.task_name)

# 创建logger
log = MyLogger(log_dir=proj_path, **opt.log)
log.log_opt(opt)

# ===== 数据预处理 =====
# 假设data已经加载好，shape为(时间步, 股票数量)
print(f"数据形状: {data.shape}")
print(f"时间步数: {data.shape[0]}")
print(f"股票数量: {data.shape[1]}")

# 数据标准化（重要！股票价格差异很大）
# 使用z-score标准化
# data_mean = np.nanmean(data, axis=0, keepdims=True)
# data_std = np.nanstd(data, axis=0, keepdims=True)
# data_normalized = (data - data_mean) / (data_std + 1e-8)

# 处理缺失值
# 创建mask：1表示有数据，0表示缺失
mask = ~np.isnan(data)
data_normalized = np.nan_to_num(data, 0)  # 将NaN替换为0
# data_normalized = np.nan_to_num(data_normalized, 0)  # 将NaN替换为0

print(f"数据缺失率: {1 - mask.mean():.2%}")

# 可视化部分数据和缺失情况
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

# 显示前5只股票的前200个时间步
n_stocks_show = min(5, data.shape[1])
n_time_show = min(200, data.shape[0])

for i in range(n_stocks_show):
    ax1.plot(data_normalized[:n_time_show, i], alpha=0.7, label=f'Stock {i + 1}')
ax1.set_title('normalized price (first 200 time steps)')
ax1.set_xlabel('time step')
ax1.set_ylabel('standardized price')
ax1.legend()
ax1.grid(True, alpha=0.3)

# 显示缺失值模式
# ax2.imshow(mask[:n_time_show, :n_stocks_show].T, aspect='auto', cmap='RdBu')
# ax2.set_title('missing mode(blue=missing, red=available)')
# ax2.set_xlabel('time step')
# ax2.set_ylabel('stock number')
#
# plt.tight_layout()
# plt.show()

# ===== 运行CUTS+算法 =====
print("\n开始运行CUTS+算法...")
print(f"配置参数:")
print(f"- 输入步数: {opt.sota.cuts_plus.input_step}")
print(f"- 预测步数: {opt.sota.cuts_plus.data_pred.pred_step}")
print(f"- 训练轮数: {opt.sota.cuts_plus.total_epoch}")
print(f"- 批次大小: {opt.sota.cuts_plus.batch_size}")

# 运行CUTS+
# 注意：真实数据没有ground truth因果图，传入None
# graph = cuts_plus.main(
#     data,
#     mask,
#     None,  # 没有真实因果图
#     opt.sota.cuts_plus,
#     log,
#     device=device
# )

# 归一化因果图
# graph = (graph - np.min(graph)) / (np.max(graph) - np.min(graph))
# data: 形状 T×C（比如股价或你处理后的收益序列）
out = build_multiscale_views(
    data,
    top_k=3,  # 取几个主尺度
    min_period=8,  # 最小周期（按你的采样粒度设置）
    max_period=None,  # 默认为 T//2
    band_ratio=0.2,  # 频带相对宽度（中心频点±20%）
    smooth=5,  # 频谱平滑窗口
    merge_harmonics=True,
    harmonic_tol=0.1,
    max_harmonic=4,
    preproc='log_return',  # 价格数据推荐；也可 'diff' 或 None
    standardize=True,
    post_standardize=True,
    include_residual=False,  # 是否输出残差视图
    dtype=np.float32,
)

views = out["views"]  # OrderedDict: { 'scale_24': (T×C), 'scale_48': (T×C), ... }
meta = out["meta"]  # 记录峰值索引、近似周期、频带等信息（可用于日志/可视化）

graphs = {}
for name, Xs in views.items():
    # 你的 mask（若无缺失可用 np.ones_like(Xs, dtype=bool)）
    # mask = np.ones_like(Xs, dtype=bool)
    graph = cuts_plus.main(
        Xs,  # 每个尺度一份 T×C 的视图
        mask,
        None,  # 没有真实因果图
        opt.sota.cuts_plus,
        log,
        device=device
    )
    # i want to print the graph in the console, but i don't know what is the correct command, graph is a figure
    graphs[name] = graph
    show_graph(graph, name=f"cuts_graph@{name}")
graph.shape
# ===== 结果可视化 =====
print("\n生成的因果图:")

# 确保数据是正方形矩阵
print(f"图形数据维度: {graph.shape}")

# 如果graph不是正方形，使用graph而不是data
if graph.shape[0] != graph.shape[1]:
    print("警告：因果图不是正方形矩阵!")
    print(f"实际维度: {graph.shape[0]} x {graph.shape[1]}")

# 绘制完整因果图 - 使用灰度图
fig, ax = plt.subplots(figsize=(12, 12))  # 设置相等的宽高

# 使用灰度colormap，0=白色，1=黑色
im = ax.imshow(graph, cmap='gray_r', vmin=0, vmax=1, aspect='equal')
ax.set_title('Causal Matrix (88×88)', fontsize=16, pad=20)
ax.set_xlabel('Affected Stock Index', fontsize=14)
ax.set_ylabel('Causal Stock Index', fontsize=14)

# 设置主要刻度（每10个股票显示一次）
major_ticks = np.arange(0, graph.shape[0], 10)
ax.set_xticks(major_ticks)
ax.set_yticks(major_ticks)
ax.set_xticklabels([f'{i}' for i in major_ticks])
ax.set_yticklabels([f'{i}' for i in major_ticks])

# 添加细网格（可选，对于88x88可能太密）
# ax.grid(True, alpha=0.1, linewidth=0.5)

# 添加颜色条
cbar = plt.colorbar(im, ax=ax, shrink=0.8)
cbar.set_label('Causal Strength\n(White=0, Black=1)', fontsize=12)

plt.tight_layout()
plt.show()

# 额外绘制一个简洁版本
fig2, ax2 = plt.subplots(figsize=(10, 10))

# 简洁的灰度热力图
im2 = ax2.imshow(graph, cmap='gray_r', vmin=0, vmax=1, aspect='equal')
ax2.set_title('Causal Matrix (Simplified)', fontsize=16)
ax2.set_xlabel('Affected Stock Index', fontsize=12)
ax2.set_ylabel('Causal Stock Index', fontsize=12)

# 只在边缘显示刻度
ax2.set_xticks([0, 20, 40, 60, 80])
ax2.set_yticks([0, 20, 40, 60, 80])

# 添加颜色条
cbar2 = plt.colorbar(im2, ax=ax2, shrink=0.8)
cbar2.set_label('Causal Strength', fontsize=12)

plt.tight_layout()
plt.show()

# 找出最强的因果关系
threshold = 0.5  # 可调整阈值
strong_connections = np.where(graph > threshold)
print(f"\n强因果关系（阈值>{threshold}）:")
for i, j in zip(strong_connections[0], strong_connections[1]):
    if i != j:  # 排除自身因果
        print(f"股票{i + 1} → 股票{j + 1}: 强度={graph[i, j]:.3f}")

# 统计每只股票的影响力
out_degree = graph.sum(axis=1) - np.diag(graph)  # 排除自身
in_degree = graph.sum(axis=0) - np.diag(graph)

print(f"\n股票影响力排名（出度）:")
for idx in np.argsort(out_degree)[::-1][:10]:  # 前10名
    print(f"股票{idx + 1}: {out_degree[idx]:.3f}")

print(f"\n最受影响的股票（入度）:")
for idx in np.argsort(in_degree)[::-1][:10]:  # 前10名
    print(f"股票{idx + 1}: {in_degree[idx]:.3f}")

# 保存结果
np.save(opj(proj_path, 'causal_graph.npy'), graph)
print(f"\n结果已保存到: {proj_path}")
# 添加这行：确保因果图在正确的设备上
if hasattr(graph, 'cpu'):
    graph = graph.cpu().numpy()
    print("graph是在cpu上，已转成numpy")  # 先转为numpy

if torch.cuda.is_available():
    device = 'cuda'
    print(f'使用GPU: {torch.cuda.get_device_name(0)}')
else:
    device = 'cpu'
    print('使用CPU')

# 设置随机种子
torch.manual_seed(42)
np.random.seed(42)
if torch.cuda.is_available():
    torch.cuda.manual_seed(42)

graph = torch.tensor(graph, dtype=torch.float32).to(device)
# 创建模型实例，传入因果图
model = Model(graph=graph)
model.to(device)

# 打印模型信息
total_params = sum(p.numel() for p in model.parameters())
trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)

print(f"模型创建成功！")
print(f"模型名称: {model.model_name}")
print(f"总参数量: {total_params:,}")
print(f"可训练参数: {trainable_params:,}")
print(f"因果图维度: {model.graph.shape}")
print(f"因果变量维度: {model.causal_z_size}")

print("开始训练模型...")

# 设置训练参数
silence_step = 0  # 开始打印日志的步数
skip_step = 20  # 验证和保存的间隔步数
import torch

torch.autograd.set_detect_anomaly(True)
print("✓ 异常检测已启用")
# 创建执行器
executor = Executor(model, silence_step=silence_step, skip_step=skip_step, device=device)

# 2. 创建一个包装函数来安全地训练
def safe_train_step(model, optimizer, batch_dict):
    """安全的训练步骤，包含详细的错误处理"""
    try:
        optimizer.zero_grad()

        # 检查输入张量
        print("检查输入张量设备...")
        for key, value in batch_dict.items():
            if torch.is_tensor(value):
                print(f"{key}: {value.device}, shape: {value.shape}, dtype: {value.dtype}")

        # 前向传播
        print("开始前向传播...")
        outputs = model(
            word_ph=batch_dict['word_batch'],
            price_ph=batch_dict['price_batch'],
            stock_ph=batch_dict['stock_batch'],
            T_ph=batch_dict['T_batch'],
            n_words_ph=batch_dict['n_words_batch'],
            n_msgs_ph=batch_dict['n_msgs_batch'],
            y_ph=batch_dict['y_batch'],
            ss_index_ph=batch_dict['ss_index_batch'],
            is_training=True
        )
        print("✓ 前向传播完成")

        # 检查输出张量
        print("检查输出张量...")
        for key, value in outputs.items():
            if torch.is_tensor(value):
                print(f"Output {key}: {value.device}, shape: {value.shape}, requires_grad: {value.requires_grad}")

        # 计算损失
        print("计算损失...")
        loss = model.compute_loss(outputs, batch_dict['T_batch'])
        print(f"✓ 损失计算完成: {loss.item()}")

        # 检查损失
        if torch.isnan(loss) or torch.isinf(loss):
            print(f"❌ 损失异常: {loss}")
            return None, None

        # 反向传播
        print("开始反向传播...")
        loss.backward()
        print("✓ 反向传播完成")

        # 检查梯度
        print("检查梯度...")
        for name, param in model.named_parameters():
            if param.grad is not None:
                grad_norm = param.grad.norm()
                if torch.isnan(grad_norm) or torch.isinf(grad_norm):
                    print(f"❌ 参数 {name} 梯度异常: {grad_norm}")
                    return None, None
                elif grad_norm > 100:  # 梯度过大
                    print(f"⚠️ 参数 {name} 梯度较大: {grad_norm}")
            else:
                print(f"⚠️ 参数 {name} 没有梯度")

        # 梯度裁剪
        torch.nn.utils.clip_grad_norm_(model.parameters(), model.clip)

        # 优化步骤
        optimizer.step()
        model.step_global_step()

        return loss, outputs

    except RuntimeError as e:
        print(f"❌ 训练步骤出错: {e}")
        print("详细错误信息:")
        import traceback
        traceback.print_exc()
        return None, None


# 3. 修改执行器的训练循环（替换原来的train_and_dev方法）
def debug_train_and_dev(executor):
    """调试版本的训练函数"""
    # 初始化词向量表
    word_table_init = executor.pipe.init_word_table()
    executor.model.init_word_table(word_table_init)
    print('✓ 词向量表初始化完成')

    # 检查点恢复（简化版）
    print('✓ 开始新的训练会话')

    # 确保模型在训练模式
    executor.model.train()

    # 获取一个训练批次进行测试
    print("获取训练数据...")
    train_batch_gen = executor.pipe.batch_gen(phase='train')

    try:
        train_batch_dict = next(train_batch_gen)
        print(f"✓ 获取批次数据，batch_size: {train_batch_dict['batch_size']}")
    except Exception as e:
        print(f"❌ 获取训练数据失败: {e}")
        return

    # 转换为张量
    train_batch_dict = executor._to_tensor(train_batch_dict)
    print("✓ 数据转换为张量完成")

    # 进行一步安全训练测试
    print("\n" + "=" * 50)
    print("开始安全训练测试")
    print("=" * 50)

    loss, outputs = safe_train_step(executor.model, executor.optimizer, train_batch_dict)

    if loss is not None:
        print(f"✅ 训练步骤成功! 损失: {loss.item():.6f}")

        # 计算准确率
        if outputs['y_T'] is not None and outputs['y_T_'] is not None:
            pred = outputs['y_T'].detach().cpu().numpy()
            true = outputs['y_T_'].detach().cpu().numpy()
            correct = np.sum(np.argmax(pred, axis=1) == np.argmax(true, axis=1))
            accuracy = correct / len(pred)
            print(f"✅ 批次准确率: {accuracy:.3f} ({correct}/{len(pred)})")

        # 如果成功，继续正常训练
        print("\n" + "=" * 50)
        print("单步测试成功，开始正常训练...")
        print("=" * 50)

        # 进行几个epoch的训练
        for epoch in range(min(3, executor.model.n_epochs)):  # 先只训练3个epoch测试
            print(f'\nEpoch {epoch + 1} 开始')

            train_batch_gen = executor.pipe.batch_gen(phase='train')
            epoch_losses = []
            batch_count = 0

            for train_batch_dict in train_batch_gen:
                batch_count += 1
                if batch_count > 10:  # 每个epoch只训练10个batch进行测试
                    break

                train_batch_dict = executor._to_tensor(train_batch_dict)

                # 使用简化的训练步骤
                executor.optimizer.zero_grad()

                outputs = executor.model(
                    word_ph=train_batch_dict['word_batch'],
                    price_ph=train_batch_dict['price_batch'],
                    stock_ph=train_batch_dict['stock_batch'],
                    T_ph=train_batch_dict['T_batch'],
                    n_words_ph=train_batch_dict['n_words_batch'],
                    n_msgs_ph=train_batch_dict['n_msgs_batch'],
                    y_ph=train_batch_dict['y_batch'],
                    ss_index_ph=train_batch_dict['ss_index_batch'],
                    is_training=True
                )

                loss = executor.model.compute_loss(outputs, train_batch_dict['T_batch'])
                loss.backward()

                torch.nn.utils.clip_grad_norm_(executor.model.parameters(), executor.model.clip)
                executor.optimizer.step()
                executor.model.step_global_step()

                epoch_losses.append(loss.item())

                if batch_count % 5 == 0:
                    print(f"  Batch {batch_count}, Loss: {loss.item():.6f}")

            avg_loss = np.mean(epoch_losses)
            print(f"Epoch {epoch + 1} 完成, 平均损失: {avg_loss:.6f}")

        print("\n✅ 调试训练完成!")

    else:
        print("❌ 训练步骤失败，请检查上面的错误信息")

print("开始调试训练...")
debug_train_and_dev(executor)





try:
    # 开始训练
    print("=" * 60)
    print("开始训练阶段")
    print("=" * 60)

    executor.train_and_dev()

    print("=" * 60)
    print("训练完成！开始测试...")
    print("=" * 60)

    # 测试模型
    executor.restore_and_test()

    print("=" * 60)
    print("模型训练和测试完成！")
    print("=" * 60)

except KeyboardInterrupt:
    print("训练被用户中断")
except Exception as e:
    print(f"训练过程中发生错误: {e}")
    import traceback

    traceback.print_exc()

# ================================
# 第7步：预测分析和因果关系分析
# ================================
print("开始进行预测分析和因果关系分析...")

try:
    # 创建预测查看器
    viewer = StockPredictionViewer(device=device)

    # 进行全面预测分析（包含因果分析）
    print("正在进行所有股票的预测分析...")
    predictions, causal_analysis = viewer.predict_all_stocks(phase='test', save_to_file=True)

    if predictions and causal_analysis:
        print("\n" + "=" * 60)
        print("预测结果摘要")
        print("=" * 60)

        # 计算整体准确率
        total_correct = sum(p['correct_predictions'] for p in predictions.values())
        total_samples = sum(p['total_predictions'] for p in predictions.values())
        overall_accuracy = total_correct / total_samples if total_samples > 0 else 0

        print(f"总体准确率: {overall_accuracy:.3f}")
        print(f"预测股票数量: {len(predictions)}")

        # 显示表现最好的股票
        sorted_stocks = sorted(predictions.items(),
                               key=lambda x: x[1]['accuracy'], reverse=True)

        print("\n表现最好的前5只股票:")
        for i, (stock, data) in enumerate(sorted_stocks[:5]):
            print(
                f"{i + 1}. {stock}: {data['accuracy']:.3f} ({data['correct_predictions']}/{data['total_predictions']})")

        print("\n" + "=" * 60)
        print("因果关系分析结果")
        print("=" * 60)

        if causal_analysis:
            causal_stats = causal_analysis['causal_graph_stats']
            print(f"因果图连接数: {causal_stats['total_connections']}")
            print(f"图稀疏度: {causal_stats['sparsity']:.4f}")
            print(f"最大影响强度: {causal_stats['max_influence']:.4f}")
            print(f"平均影响强度: {causal_stats['mean_influence']:.4f}")

            # 显示因果影响最强的股票
            if 'stock_influences' in causal_analysis:
                stock_influences = causal_analysis['stock_influences']
                sorted_influences = sorted(stock_influences.items(),
                                           key=lambda x: x[1]['influence_strength'], reverse=True)

                print("\n因果影响最强的前5只股票:")
                for i, (stock, influence) in enumerate(sorted_influences[:5]):
                    print(f"{i + 1}. {stock}: 影响强度 {influence['influence_strength']:.4f}")

            # 显示强相关的股票对
            if 'cross_stock_correlations' in causal_analysis:
                strong_corrs = causal_analysis['cross_stock_correlations'].get('strong_correlations', [])
                if strong_corrs:
                    print(f"\n发现 {len(strong_corrs)} 对强因果关联的股票:")
                    for corr in strong_corrs[:5]:  # 显示前5对
                        print(
                            f"{corr['stock1']} - {corr['stock2']}: {corr['correlation']:.3f} ({corr['relationship_type']})")

        # 可视化因果图
        print("\n正在生成因果图可视化...")
        viewer.visualize_causal_graph(top_k=30, save_path='causal_graph_analysis.png')

        # 分析特定股票的预测归因（如果AAPL存在）
        if 'AAPL' in predictions:
            print("\n" + "=" * 60)
            print("AAPL 预测归因分析")
            print("=" * 60)

            attribution = viewer.analyze_prediction_attribution('AAPL', sample_idx=0)
            if attribution:
                pred_info = attribution['prediction_info']
                print(f"预测方向: {pred_info['predicted_direction']}")
                print(f"实际方向: {pred_info['actual_direction']}")
                print(f"预测置信度: {pred_info['prediction_confidence']:.3f}")
                print(f"预测正确: {pred_info['prediction_correct']}")

                if attribution['causal_features']:
                    causal_strength = np.linalg.norm(attribution['causal_features'])
                    print(f"因果影响强度: {causal_strength:.4f}")

                if attribution['attention_weights']:
                    att_weights = np.array(attribution['attention_weights'])
                    max_att_day = np.argmax(att_weights)
                    print(f"最重要的历史天数: 第{max_att_day + 1}天 (权重: {att_weights[max_att_day]:.3f})")

        print("\n" + "=" * 60)
        print("分析完成！详细结果已保存到文件")
        print("=" * 60)

    else:
        print("预测分析失败，请检查模型状态")

except Exception as e:
    print(f"预测分析过程中发生错误: {e}")
    import traceback

    traceback.print_exc()

# ================================
# 第8步：生成分析报告
# ================================
print("\n正在生成综合分析报告...")

# 创建分析报告
report = {
    "实验配置": {
        "因果图维度": graph.shape,
        "因果图稀疏度": float(np.count_nonzero(graph) / graph.size),
        "设备": device,
        "模型名称": model.model_name if 'model' in locals() else "未知"
    },
    "训练结果": {
        "是否完成训练": "executor" in locals(),
        "模型参数量": total_params if 'total_params' in locals() else 0
    },
    "预测性能": {
        "整体准确率": overall_accuracy if 'overall_accuracy' in locals() else 0,
        "预测股票数": len(predictions) if 'predictions' in locals() and predictions else 0
    },
    "因果分析": {
        "因果模块启用": model.graph is not None if 'model' in locals() else False,
        "分析完成": causal_analysis is not None if 'causal_analysis' in locals() else False
    }
}

print("=" * 60)
print("实验综合报告")
print("=" * 60)
for category, items in report.items():
    print(f"\n{category}:")
    for key, value in items.items():
        print(f"  {key}: {value}")

# 保存报告
import json
from datetime import datetime

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
report_path = f'experiment_report_{timestamp}.json'

with open(report_path, 'w', encoding='utf-8') as f:
    json.dump(report, f, indent=2, ensure_ascii=False, default=str)

print(f"\n实验报告已保存到: {report_path}")

print("\n" + "=" * 60)
print("🎉 完整的因果图股票预测实验已完成！")
print("=" * 60)
print("生成的文件:")
print("1. causal_graph.npy - 因果图数据")
print("2. causal_graph_analysis.png - 因果图可视化")
print("3. stock_predictions_with_causal_test_*.json - 详细预测结果")
print("4. experiment_report_*.json - 实验综合报告")
print("5. checkpoints/ - 模型检查点文件")
print("=" * 60)