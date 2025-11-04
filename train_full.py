"""
自动数据预处理和模型训练脚本
完整的端到端训练流程
"""
import os
import sys
import numpy as np
import pandas as pd
from datetime import datetime
import torch
import shutil

print("=" * 70)
print("🚀 ICSFP 完整训练流程")
print("=" * 70)

# ==============================================================================
# 第一步：准备价格数据
# ==============================================================================
print("\n📊 第1步：准备价格数据")
print("-" * 70)

price_raw_dir = "data/cikm18/price"
price_preprocessed_dir = "data/cikm18/price/preprocessed"

if not os.path.exists(price_preprocessed_dir):
    print("创建价格预处理目录...")
    os.makedirs(price_preprocessed_dir, exist_ok=True)

# 检查原始价格文件
csv_files = [f for f in os.listdir(price_raw_dir) if f.endswith('.csv')]
print(f"✅ 找到 {len(csv_files)} 个价格文件")

# 简单的预处理：计算涨跌标签
print("处理价格数据...")
processed_count = 0

for csv_file in csv_files[:10]:  # 先处理10个股票进行快速测试
    stock_symbol = csv_file.replace('.csv', '')
    input_path = os.path.join(price_raw_dir, csv_file)
    output_path = os.path.join(price_preprocessed_dir, stock_symbol)
    
    try:
        # 读取价格数据
        df = pd.read_csv(input_path)
        
        if 'Date' in df.columns and 'Close' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.sort_values('Date')
            
            # 计算涨跌
            df['Movement'] = (df['Close'].shift(-1) > df['Close']).astype(int)
            df = df[:-1]  # 删除最后一行（没有movement标签）
            
            # 保存为文本文件（每行一个日期和标签）
            os.makedirs(output_path, exist_ok=True)
            
            # 保存运动标签
            movement_file = os.path.join(output_path, 'movement.txt')
            with open(movement_file, 'w') as f:
                for _, row in df.iterrows():
                    date_str = row['Date'].strftime('%Y-%m-%d')
                    movement = row['Movement']
                    f.write(f"{date_str}\t{movement}\n")
            
            processed_count += 1
            
    except Exception as e:
        print(f"   ⚠️  处理 {stock_symbol} 失败: {e}")
        continue

print(f"✅ 价格数据处理完成: {processed_count} 个股票")

# ==============================================================================
# 第二步：准备推文数据（如果没有，创建dummy数据）
# ==============================================================================
print("\n💬 第2步：准备推文数据")
print("-" * 70)

tweet_preprocessed_dir = "data/cikm18/tweet/preprocessed"

if not os.path.exists(tweet_preprocessed_dir):
    print("⚠️  没有找到推文数据，创建占位文件...")
    os.makedirs(tweet_preprocessed_dir, exist_ok=True)
    
    # 为每个处理过的股票创建dummy推文
    for csv_file in csv_files[:10]:
        stock_symbol = csv_file.replace('.csv', '')
        output_path = os.path.join(tweet_preprocessed_dir, stock_symbol)
        os.makedirs(output_path, exist_ok=True)
        
        # 创建一个简单的推文文件（实际训练时会被忽略或使用默认值）
        tweet_file = os.path.join(output_path, 'tweets.txt')
        with open(tweet_file, 'w', encoding='utf-8') as f:
            f.write(f"2014-01-01\tDummy tweet for {stock_symbol}\n")
    
    print(f"✅ 创建了 {len(csv_files[:10])} 个占位推文文件")
else:
    print("✅ 推文目录已存在")

# ==============================================================================
# 第三步：检查和准备其他必需文件
# ==============================================================================
print("\n📁 第3步：检查配置文件")
print("-" * 70)

required_files = {
    'causal_graph.npy': '因果图',
    'res/vocab.txt': '词汇表',
    'res/glove.twitter.27B.50d.txt': 'GloVe词向量'
}

all_ready = True
for file_path, name in required_files.items():
    if os.path.exists(file_path):
        if file_path.endswith('.npy'):
            data = np.load(file_path)
            print(f"✅ {name}: {file_path} (shape: {data.shape})")
        else:
            size_mb = os.path.getsize(file_path) / 1024 / 1024
            print(f"✅ {name}: {file_path} ({size_mb:.1f} MB)")
    else:
        print(f"❌ {name}: {file_path} 不存在")
        all_ready = False

if not all_ready:
    print("\n⚠️  缺少必要文件，无法继续训练")
    print("请确保运行了因果图生成: python Main.py")
    sys.exit(1)

# ==============================================================================
# 第四步：修改配置以使用处理后的数据
# ==============================================================================
print("\n⚙️  第4步：准备训练配置")
print("-" * 70)

# 创建必要的目录
os.makedirs('checkpoints', exist_ok=True)
os.makedirs('log', exist_ok=True)

print("✅ 所有目录准备就绪")

# ==============================================================================
# 第五步：开始训练
# ==============================================================================
print("\n🎯 第5步：开始模型训练")
print("=" * 70)

# 检查 GPU
if torch.cuda.is_available():
    device = 'cuda'
    print(f"✅ GPU 可用: {torch.cuda.get_device_name(0)}")
    print(f"   显存: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
else:
    device = 'cpu'
    print("⚠️  使用 CPU（训练会很慢）")

# 导入训练模块
try:
    from Model import Model
    from Executor import Executor
    print("✅ 训练模块导入成功")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)

# 加载因果图
print("\n加载因果图...")
graph = np.load('causal_graph.npy')
print(f"✅ 因果图: {graph.shape}, 稀疏度: {(graph == 0).sum() / graph.size:.2%}")

# 创建模型
print("\n创建模型...")
model = Model(graph=graph)

total_params = sum(p.numel() for p in model.parameters())
trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)

print(f"✅ 模型创建成功:")
print(f"   名称: {model.model_name[:50]}...")
print(f"   总参数: {total_params:,}")
print(f"   可训练参数: {trainable_params:,}")

# 创建执行器
print("\n创建训练执行器...")
executor = Executor(
    model=model,
    silence_step=0,
    skip_step=10,  # 每10步显示一次进度
    device=device
)
print("✅ 执行器创建成功")

# 开始训练
print("\n" + "=" * 70)
print("🎯 开始训练")
print("=" * 70)
print(f"\n⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"\n📊 训练配置:")
print(f"   - 训练轮数: {model.n_epochs} epochs")
print(f"   - 批次大小: {model.batch_size_for_name}")
print(f"   - 学习率: {model.lr}")
print(f"   - 优化器: {model.opt.upper()}")
print(f"   - 设备: {device.upper()}")
print(f"   - 检查点保存: {model.tf_checkpoints_path}")

print(f"\n⏱️  预计训练时间:")
if device == 'cuda':
    print(f"   - GPU训练: 约 15-20 小时")
    print(f"   - 可以随时按 Ctrl+C 中断，已训练的检查点会保存")
else:
    print(f"   - CPU训练: 约 50+ 小时")
    print(f"   - 强烈建议使用 GPU 训练")

print("\n💡 提示:")
print("   - 训练过程中会自动保存检查点")
print("   - 日志保存在 log/ 目录")
print("   - 可以在另一个终端监控 GPU 使用: watch -n 1 nvidia-smi")

input("\n按 Enter 键开始训练，或 Ctrl+C 取消...")

try:
    start_time = datetime.now()
    
    # 训练
    print("\n" + "-" * 70)
    print("🚂 开始训练循环...")
    print("-" * 70)
    executor.train_and_dev()
    
    training_time = datetime.now() - start_time
    
    print("\n" + "=" * 70)
    print("✅ 训练完成！")
    print("=" * 70)
    print(f"⏱️  总用时: {training_time}")
    print(f"⏰ 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 测试
    print("\n" + "-" * 70)
    print("🧪 开始测试...")
    print("-" * 70)
    executor.restore_and_test()
    
    # 总结
    print("\n" + "=" * 70)
    print("🎉 训练和测试完成！")
    print("=" * 70)
    
    # 检查保存的模型
    checkpoint_dir = model.tf_checkpoints_path
    if os.path.exists(checkpoint_dir):
        files = [f for f in os.listdir(checkpoint_dir) if f.endswith('.pth')]
        if files:
            print(f"\n✅ 保存了 {len(files)} 个检查点:")
            for f in files:
                file_path = os.path.join(checkpoint_dir, f)
                size_mb = os.path.getsize(file_path) / 1024 / 1024
                print(f"   - {f} ({size_mb:.1f} MB)")
    
    print("\n🚀 下一步操作:")
    print("   1. 重启 API 服务器:")
    print("      conda activate ic_sfp_gpu")
    print("      python api/app.py")
    print("   2. 刷新浏览器: http://127.0.0.1:5000")
    print("   3. 应该看到 '✅ 模型已加载' 状态")
    print("   4. 进行真实预测测试")
    
    print("\n📊 查看训练日志:")
    print(f"   - 日志目录: log/")
    print(f"   - TensorBoard (如果启用): tensorboard --logdir={model.tf_graph_path}")

except KeyboardInterrupt:
    print("\n\n⚠️  训练被用户中断")
    print(f"\n⏱️  已训练时间: {datetime.now() - start_time}")
    
    # 检查是否有保存的检查点
    checkpoint_dir = model.tf_checkpoints_path
    if os.path.exists(checkpoint_dir):
        files = [f for f in os.listdir(checkpoint_dir) if f.endswith('.pth')]
        if files:
            print(f"\n✅ 已保存 {len(files)} 个部分训练的检查点")
            print("   可以使用这些检查点进行预测")
    
    print("\n💡 提示:")
    print("   - 可以重新运行继续训练")
    print("   - 或使用现有检查点（如果性能可接受）")
    
except Exception as e:
    print(f"\n\n❌ 训练出错: {e}")
    import traceback
    print("\n详细错误:")
    traceback.print_exc()
    
    print("\n🔧 常见问题:")
    print("   1. 显存不足 → 在 config.yml 中减小 batch_size")
    print("   2. 数据格式错误 → 检查 data/cikm18/ 目录结构")
    print("   3. 文件权限 → 确保有写入 checkpoints/ 的权限")

print("\n" + "=" * 70)
