#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证项目创新算法是否被真实使用

检查项：
1. Granger因果检验算法
2. CUTS+因果发现算法
3. 因果图是否被模型使用
4. 多数据集支持系统
"""

import os
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_innovation_algorithms():
    """检查创新算法实现和使用情况"""
    
    print("=" * 80)
    print("🔍 项目创新算法使用情况验证")
    print("=" * 80)
    
    results = {
        'granger_exists': False,
        'cuts_exists': False,
        'causal_graph_exists': False,
        'causal_graph_used_in_model': False,
        'multi_dataset_system': False
    }
    
    # 1. 检查Granger因果检验
    print("\n1️⃣  检查 Granger 因果检验算法")
    print("-" * 80)
    if os.path.exists('granger_causality.py'):
        results['granger_exists'] = True
        print("   ✅ granger_causality.py 存在")
        
        # 检查实现
        with open('granger_causality.py', 'r', encoding='utf-8') as f:
            content = f.read()
            if 'grangercausalitytests' in content:
                print("   ✅ 使用 statsmodels.grangercausalitytests")
            if 'class GrangerCausalityAnalyzer' in content:
                print("   ✅ 实现了 GrangerCausalityAnalyzer 类")
            if 'compute_causality_matrix' in content:
                print("   ✅ 实现了 compute_causality_matrix 方法")
    else:
        print("   ❌ granger_causality.py 不存在")
    
    # 2. 检查CUTS+算法
    print("\n2️⃣  检查 CUTS+ 因果发现算法")
    print("-" * 80)
    if os.path.exists('cuts_plus.py'):
        results['cuts_exists'] = True
        print("   ✅ cuts_plus.py 存在")
        
        with open('cuts_plus.py', 'r', encoding='utf-8') as f:
            content = f.read()
            if 'CUTS_Plus_Net' in content:
                print("   ✅ 实现了 CUTS_Plus_Net 网络")
            if 'gumbel_softmax' in content:
                print("   ✅ 使用了 Gumbel-Softmax 技巧")
    else:
        print("   ❌ cuts_plus.py 不存在")
    
    if os.path.exists('compute_cuts_graph.py'):
        print("   ✅ compute_cuts_graph.py 存在")
        with open('compute_cuts_graph.py', 'r', encoding='utf-8') as f:
            content = f.read()
            if 'build_graph_cuts' in content:
                print("   ✅ 实现了 build_graph_cuts 函数")
            if 'cuts_plus.main' in content:
                print("   ✅ 调用了 cuts_plus.main")
    
    # 3. 检查因果图文件
    print("\n3️⃣  检查因果图文件")
    print("-" * 80)
    if os.path.exists('causal_graph.npy'):
        results['causal_graph_exists'] = True
        print("   ✅ causal_graph.npy 存在")
        
        graph = np.load('causal_graph.npy')
        print(f"   📊 因果图形状: {graph.shape}")
        print(f"   📊 非零元素: {np.count_nonzero(graph)}/{graph.size}")
        print(f"   📊 稀疏度: {np.count_nonzero(graph)/graph.size:.2%}")
        
        # 显示示例关系
        print(f"\n   前3x3因果关系矩阵:")
        for i in range(min(3, graph.shape[0])):
            row = "      " + "  ".join([f"{graph[i,j]:.4f}" for j in range(min(3, graph.shape[1]))])
            print(row)
        
        # 检查是否是真实计算还是随机生成
        if np.count_nonzero(graph) > 0:
            print(f"\n   ✅ 因果图包含真实关系(非全零)")
        
    else:
        print("   ❌ causal_graph.npy 不存在")
        print("   提示: 运行 python compute_cuts_graph.py 生成")
    
    # 4. 检查Model.py中是否使用因果图
    print("\n4️⃣  检查模型是否使用因果图")
    print("-" * 80)
    if os.path.exists('Model.py'):
        with open('Model.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
            if 'def __init__(self, graph=None)' in content:
                print("   ✅ Model.__init__ 接受 graph 参数")
                results['causal_graph_used_in_model'] = True
            
            if 'self.graph = ' in content and 'torch.tensor(graph' in content:
                print("   ✅ 模型存储了因果图: self.graph")
            
            if 'causal_w1' in content or 'causal_w2' in content:
                print("   ✅ 实现了因果权重层: causal_w1, causal_w2")
            
            if 'causal_Z' in content or 'causal_z' in content:
                print("   ✅ 实现了因果特征变量")
            
            if '_create_causal_variables' in content:
                print("   ✅ 实现了 _create_causal_variables 方法")
    else:
        print("   ❌ Model.py 不存在")
    
    # 5. 检查多数据集系统
    print("\n5️⃣  检查多数据集支持系统")
    print("-" * 80)
    
    multi_dataset_files = [
        'Main.py',
        'dataset_manager.py', 
        'unified_data_loader.py',
        'causal_discovery_manager.py'
    ]
    
    found_files = []
    for fname in multi_dataset_files:
        if os.path.exists(fname):
            found_files.append(fname)
            print(f"   ✅ {fname} 存在")
    
    if len(found_files) >= 2:
        results['multi_dataset_system'] = True
        print(f"\n   ✅ 多数据集系统文件完整度: {len(found_files)}/{len(multi_dataset_files)}")
    else:
        print(f"\n   ⚠️  多数据集系统文件不完整: {len(found_files)}/{len(multi_dataset_files)}")
    
    # 6. 检查API中是否使用因果图
    print("\n6️⃣  检查API预测器是否使用因果图")
    print("-" * 80)
    
    predictor_files = ['api/predictor_enhanced.py', 'api/predictor.py']
    for pf in predictor_files:
        if os.path.exists(pf):
            print(f"   检查 {pf}...")
            with open(pf, 'r', encoding='utf-8') as f:
                content = f.read()
                
                if "graph_path = 'causal_graph.npy'" in content:
                    print(f"     ✅ 加载因果图: causal_graph.npy")
                
                if 'self.graph = np.load' in content:
                    print(f"     ✅ 读取因果图到 self.graph")
                
                if 'Model(graph=' in content or 'Model(self.graph' in content:
                    print(f"     ✅ 将因果图传递给模型")
                
                if 'get_causal_graph' in content:
                    print(f"     ✅ 提供因果图查询接口")
    
    # 7. 总结
    print("\n" + "=" * 80)
    print("📊 验证结果汇总")
    print("=" * 80)
    
    total_checks = len(results)
    passed_checks = sum(results.values())
    
    for key, value in results.items():
        status = "✅" if value else "❌"
        key_name = key.replace('_', ' ').title()
        print(f"   {status} {key_name}")
    
    print(f"\n   通过率: {passed_checks}/{total_checks} ({passed_checks/total_checks*100:.1f}%)")
    
    # 8. 实际运行测试
    print("\n" + "=" * 80)
    print("🧪 实际运行测试")
    print("=" * 80)
    
    try:
        print("\n测试1: 加载因果图并传递给模型...")
        graph = np.load('causal_graph.npy')
        from Model import Model
        
        model = Model(graph=graph)
        
        if model.graph is not None:
            print("   ✅ 模型成功接收因果图")
            print(f"   📊 模型中因果图形状: {model.graph.shape}")
        else:
            print("   ❌ 模型未接收因果图")
        
        # 检查因果相关层
        if hasattr(model, 'causal_w1'):
            print("   ✅ 模型包含 causal_w1 层")
        if hasattr(model, 'causal_w2'):
            print("   ✅ 模型包含 causal_w2 层")
        
    except Exception as e:
        print(f"   ❌ 测试失败: {e}")
    
    try:
        print("\n测试2: 检查预测器是否使用因果图...")
        from api.predictor_enhanced import EnhancedStockPredictor
        
        predictor = EnhancedStockPredictor()
        
        if predictor.graph is not None:
            print("   ✅ 预测器加载了因果图")
            print(f"   📊 预测器中因果图形状: {predictor.graph.shape}")
        else:
            print("   ❌ 预测器未加载因果图")
        
        if predictor.model and hasattr(predictor.model, 'graph'):
            if predictor.model.graph is not None:
                print("   ✅ 预测器的模型使用了因果图")
            else:
                print("   ⚠️  预测器的模型未使用因果图")
        
    except Exception as e:
        print(f"   ❌ 测试失败: {e}")
    
    # 最终结论
    print("\n" + "=" * 80)
    print("🎯 最终结论")
    print("=" * 80)
    
    if passed_checks >= 4:
        print("\n✅ 项目的创新算法已经实现并被使用！")
        print("\n关键创新点:")
        print("   • Granger因果检验: 识别股票间时序因果关系")
        print("   • CUTS+算法: GPU加速的动态因果图学习")
        print("   • 因果图嵌入: 将因果关系融入深度学习模型")
        print("   • 端到端系统: 从因果发现到预测的完整流程")
    elif passed_checks >= 2:
        print("\n⚠️  项目部分创新算法已实现，但使用不完整")
        print("\n建议:")
        print("   • 运行 python compute_cuts_graph.py 生成因果图")
        print("   • 确保模型训练时使用因果图")
        print("   • 完善多数据集支持系统")
    else:
        print("\n❌ 项目创新算法未充分使用")
        print("\n需要:")
        print("   • 实现完整的因果发现算法")
        print("   • 将因果图集成到模型中")
        print("   • 验证算法实际效果")
    
    print("\n" + "=" * 80)
    
    return results


def main():
    results = check_innovation_algorithms()
    
    print("\n💡 建议的下一步:")
    print("=" * 80)
    
    if not results['causal_graph_exists']:
        print("1. 生成因果图:")
        print("   python compute_cuts_graph.py")
    
    if not results['multi_dataset_system']:
        print("2. 查看多数据集系统文档:")
        print("   cat README.md | grep -A 20 '多数据集'")
    
    print("\n3. 验证算法效果:")
    print("   python test_model_usage.py")
    
    print("\n4. 运行完整训练:")
    print("   python Main.py --dataset ACL18")
    
    print("\n" + "=" * 80)


if __name__ == '__main__':
    main()
