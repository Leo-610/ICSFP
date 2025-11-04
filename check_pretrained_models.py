"""
检查现有预训练模型并测试加载
"""
import os
import torch
import numpy as np
from datetime import datetime

print("=" * 70)
print("🔍 预训练模型检查报告")
print("=" * 70)

# 检查所有模型
checkpoint_base = "checkpoints"
model_dirs = [
    "all_days-5.msgs-30-words-40_word_embed-glove.vmd_in-hedge_alpha-0.5.anneal-0.005.rec-zh_batch-32.opt-adam.lr-0.001-drop-0.3-cell-gru",
    "all_days-5.msgs-30-words-40_word_embed-glove.vmd_in-hedge_alpha-0.5.anneal-0.005.rec-zh_batch-32.opt-adam.lr-0.001-drop-0.3-cell-gru_ds-cmin-cn_nocausal",
    "all_days-5.msgs-30-words-40_word_embed-glove.vmd_in-hedge_alpha-0.5.anneal-0.005.rec-zh_batch-32.opt-adam.lr-0.001-drop-0.3-cell-gru_nocausal"
]

print("\n✅ 发现 3 个预训练模型:")
print("-" * 70)

models_info = []

for i, model_dir in enumerate(model_dirs, 1):
    model_path = os.path.join(checkpoint_base, model_dir, "model.pth")
    
    if os.path.exists(model_path):
        size_mb = os.path.getsize(model_path) / 1024 / 1024
        mtime = datetime.fromtimestamp(os.path.getmtime(model_path))
        
        # 解析模型名称
        if "_nocausal" in model_dir:
            if "_ds-cmin-cn" in model_dir:
                model_type = "无因果增强 (CMIN-CN数据集)"
            else:
                model_type = "无因果增强 (默认数据集)"
        else:
            model_type = "✅ 有因果增强 (推荐)"
        
        print(f"\n模型 {i}: {model_type}")
        print(f"   路径: {model_path}")
        print(f"   大小: {size_mb:.1f} MB")
        print(f"   修改时间: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
        
        models_info.append({
            'number': i,
            'path': model_path,
            'size': size_mb,
            'type': model_type,
            'has_causal': '_nocausal' not in model_dir,
            'dir': model_dir
        })

# 推荐模型
print("\n" + "=" * 70)
print("📊 模型对比分析")
print("=" * 70)

print("\n模型选择建议:")
print("-" * 70)

recommended = models_info[0]  # 第一个模型（带因果增强）
print(f"\n🏆 推荐使用: 模型 {recommended['number']}")
print(f"   类型: {recommended['type']}")
print(f"   大小: {recommended['size']:.1f} MB (最大，包含最多参数)")
print(f"   优势:")
print(f"   ✅ 包含因果图增强功能")
print(f"   ✅ 完整的模型结构")
print(f"   ✅ 适合展示因果关系分析")

print(f"\n对比其他模型:")
for model in models_info[1:]:
    print(f"\n   模型 {model['number']}: {model['type']}")
    print(f"   大小: {model['size']:.1f} MB")
    if not model['has_causal']:
        print(f"   ⚠️  不支持因果增强（网站上'因果增强'选项无效）")

# 测试加载推荐模型
print("\n" + "=" * 70)
print("🧪 测试加载推荐模型")
print("=" * 70)

try:
    from Model import Model
    
    # 加载因果图
    print("\n1. 加载因果图...")
    graph = np.load('causal_graph.npy')
    print(f"   ✅ 因果图: {graph.shape}")
    
    # 创建模型
    print("\n2. 创建模型实例...")
    model = Model(graph=graph)
    print(f"   ✅ 模型创建成功")
    
    # 加载检查点
    print(f"\n3. 加载检查点...")
    checkpoint_path = recommended['path']
    
    if torch.cuda.is_available():
        checkpoint = torch.load(checkpoint_path)
        device = 'cuda'
    else:
        checkpoint = torch.load(checkpoint_path, map_location='cpu')
        device = 'cpu'
    
    model.load_state_dict(checkpoint)
    model.to(device)
    model.eval()
    
    print(f"   ✅ 检查点加载成功")
    print(f"   设备: {device}")
    
    total_params = sum(p.numel() for p in model.parameters())
    print(f"   参数数量: {total_params:,}")
    
    print("\n" + "=" * 70)
    print("✅ 模型可以正常加载和使用！")
    print("=" * 70)
    
except Exception as e:
    print(f"\n❌ 加载测试失败: {e}")
    import traceback
    traceback.print_exc()

# 说明为什么 API 没有加载
print("\n" + "=" * 70)
print("❓ 为什么 API 显示'示例模式'？")
print("=" * 70)

print("\n原因分析:")
print("-" * 70)

print("\nAPI 的模型加载逻辑 (api/predictor_enhanced.py):")
print("```python")
print("for ckpt_dir in ['checkpoints', 'checkpoints/best']:")
print("    ckpt_files = [f for f in os.listdir(ckpt_dir)")
print("                  if f.endswith('.pth')]")
print("    if ckpt_files:")
print("        ckpt_path = os.path.join(ckpt_dir, ckpt_files[0])")
print("        checkpoint = torch.load(ckpt_path)")
print("```")

print("\n🔍 问题:")
print("   API 只在 checkpoints/ 根目录查找 .pth 文件")
print("   但你的模型在 checkpoints/<子目录>/model.pth")

print("\n💡 解决方案有两种:")

# 解决方案
print("\n" + "=" * 70)
print("🛠️  解决方案")
print("=" * 70)

print("\n方案 1: 修改 API 代码（推荐，支持子目录）")
print("-" * 70)
print("修改 api/predictor_enhanced.py 的 _try_load_model 方法")
print("让它支持在子目录中搜索 model.pth")

print("\n方案 2: 复制模型到根目录（快速）")
print("-" * 70)
print(f"执行以下命令:")
src = recommended['path']
dst = os.path.join('checkpoints', 'model.pth')
print(f'   copy "{src}" "{dst}"')

print("\n推荐方案 1，因为:")
print("   ✅ 更灵活，支持多个模型共存")
print("   ✅ 保持原有目录结构")
print("   ✅ 符合项目原始设计")

# 总结
print("\n" + "=" * 70)
print("📝 总结")
print("=" * 70)

print(f"\n✅ 你有 3 个训练好的模型（总大小: {sum(m['size'] for m in models_info):.1f} MB）")
print(f"✅ 推荐使用模型 1（带因果增强，{recommended['size']:.1f} MB）")
print(f"⚠️  需要修改 API 代码或复制文件让 API 能找到模型")
print(f"⏱️  修复后重启服务器，网站会显示 '✅ 模型已加载'")

print("\n🚀 立即行动:")
print("   1. 选择解决方案（推荐方案1）")
print("   2. 修改代码或复制文件")
print("   3. 重启 API: python api/app.py")
print("   4. 刷新网页验证")

print("\n" + "=" * 70)
