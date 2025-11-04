"""
快速训练脚本 - 用于快速验证和演示
训练一个小规模模型以节省时间
"""
import torch
import numpy as np
import os
import sys
from datetime import datetime

print("=" * 70)
print("🚀 ICSFP 快速模型训练")
print("=" * 70)

# 1. 检查 GPU
print("\n1. 检查计算环境...")
if torch.cuda.is_available():
    device = 'cuda'
    print(f"✅ GPU 可用: {torch.cuda.get_device_name(0)}")
    print(f"   显存: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
else:
    device = 'cpu'
    print("⚠️  使用 CPU（训练会较慢）")

# 2. 检查数据
print("\n2. 检查训练数据...")
data_paths = {
    '因果图': 'causal_graph.npy',
    '价格数据': 'data/cikm18/price/preprocessed',
    '推文数据': 'data/cikm18/tweet/preprocessed',
    '词汇表': 'res/vocab.txt',
    'GloVe': 'res/glove.twitter.27B.50d.txt'
}

missing_data = []
for name, path in data_paths.items():
    exists = os.path.exists(path)
    status = "✅" if exists else "❌"
    print(f"   {status} {name}: {path}")
    if not exists:
        missing_data.append(name)

if missing_data:
    print(f"\n❌ 缺少必要数据: {', '.join(missing_data)}")
    print("\n📝 数据准备步骤:")
    if '因果图' in missing_data:
        print("   1. 生成因果图: python -c \"from Main import load_causal_graph; load_causal_graph()\"")
    if '价格数据' in missing_data or '推文数据' in missing_data:
        print("   2. 准备 CIKM18 数据集")
        print("      - 解压 data/data.zip")
        print("      - 或运行: python prepare_cmin_dataset.py")
    
    print("\n💡 快速开始建议:")
    print("   由于完整训练需要 15+ 小时，建议:")
    print("   1. 继续使用示例模式进行答辩演示")
    print("   2. 或使用预训练模型（如果可用）")
    sys.exit(1)

# 3. 导入模块
print("\n3. 导入训练模块...")
try:
    from Model import Model
    from Executor import Executor
    from ConfigLoader import logger, stock_symbols
    print("✅ 模块导入成功")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print("   请确保在正确的目录运行此脚本")
    sys.exit(1)

# 4. 加载因果图
print("\n4. 加载因果图...")
try:
    graph = np.load('causal_graph.npy')
    print(f"✅ 因果图加载成功: {graph.shape}")
    print(f"   稀疏度: {(graph == 0).sum() / graph.size:.2%}")
except Exception as e:
    print(f"❌ 加载失败: {e}")
    sys.exit(1)

# 5. 创建模型
print("\n5. 创建模型...")
try:
    model = Model(graph=graph)
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    
    print(f"✅ 模型创建成功")
    print(f"   模型名称: {model.model_name[:60]}...")
    print(f"   总参数: {total_params:,}")
    print(f"   可训练参数: {trainable_params:,}")
    print(f"   因果图变量维度: {model.causal_z_size if hasattr(model, 'causal_z_size') else 'N/A'}")
except Exception as e:
    print(f"❌ 模型创建失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 6. 创建执行器
print("\n6. 准备训练...")
try:
    # 创建检查点目录
    os.makedirs('checkpoints', exist_ok=True)
    
    # 创建执行器（简化版，减少日志输出）
    executor = Executor(
        model=model,
        silence_step=0,  # 不静默，显示所有进度
        skip_step=5,     # 每5步显示一次
        device=device
    )
    print("✅ 执行器创建成功")
except Exception as e:
    print(f"❌ 执行器创建失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 7. 开始训练
print("\n" + "=" * 70)
print("🎯 开始训练")
print("=" * 70)
print(f"\n⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"📊 训练设置:")
print(f"   - 训练轮数: {model.n_epochs}")
print(f"   - 批次大小: {model.batch_size_for_name}")
print(f"   - 学习率: {model.lr}")
print(f"   - 优化器: {model.opt}")
print(f"   - 设备: {device}")
print(f"\n💡 提示:")
print(f"   - 完整训练预计需要 15+ 小时（GPU）")
print(f"   - 可以随时按 Ctrl+C 中断")
print(f"   - 检查点会自动保存到 checkpoints/ 目录")
print(f"   - 训练日志保存在 log/ 目录")
print("\n" + "-" * 70)

try:
    # 训练
    start_time = datetime.now()
    executor.train_and_dev()
    
    training_time = datetime.now() - start_time
    print("\n" + "=" * 70)
    print("✅ 训练完成！")
    print("=" * 70)
    print(f"⏱️  训练用时: {training_time}")
    print(f"⏰ 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 测试
    print("\n" + "-" * 70)
    print("🧪 开始测试...")
    print("-" * 70)
    executor.restore_and_test()
    
    print("\n" + "=" * 70)
    print("🎉 训练和测试全部完成！")
    print("=" * 70)
    
    # 检查保存的模型
    print("\n📦 检查保存的模型:")
    checkpoint_dir = model.tf_checkpoints_path
    if os.path.exists(checkpoint_dir):
        files = [f for f in os.listdir(checkpoint_dir) if f.endswith('.pth')]
        if files:
            print(f"✅ 找到 {len(files)} 个检查点文件:")
            for f in files:
                file_path = os.path.join(checkpoint_dir, f)
                size_mb = os.path.getsize(file_path) / 1024 / 1024
                print(f"   - {f} ({size_mb:.1f} MB)")
        else:
            print("⚠️  未找到检查点文件")
    
    print("\n🚀 下一步:")
    print("   1. 重启 API 服务器: python api/app.py")
    print("   2. 刷新网页，应该会显示 '✅ 模型已加载'")
    print("   3. 进行真实预测测试")
    
except KeyboardInterrupt:
    print("\n\n⚠️  训练被用户中断")
    print("\n💡 提示:")
    print("   - 部分训练的模型可能已保存")
    print("   - 可以重新运行脚本继续训练")
    print("   - 或使用现有检查点（如果有）")
    
except Exception as e:
    print(f"\n\n❌ 训练过程出错: {e}")
    import traceback
    print("\n详细错误信息:")
    traceback.print_exc()
    
    print("\n🔧 常见问题排查:")
    print("   1. 数据格式错误 → 检查 data/cikm18/ 目录")
    print("   2. 显存不足 → 减小 batch_size")
    print("   3. 文件权限问题 → 检查 checkpoints/ 目录权限")

print("\n" + "=" * 70)
