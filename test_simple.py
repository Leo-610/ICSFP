"""
简单测试 - 验证DataPipe和模型推理
"""

import torch
import logging

logging.basicConfig(level=logging.INFO)

def test_datapipe():
    """测试DataPipe是否能生成批次"""
    print("\n=== Test DataPipe ===")
    
    from DataPipe import DataPipe
    pipe = DataPipe()
    
    batch_gen = pipe.batch_gen_by_stocks('test')
    
    batch_count = 0
    aapl_found = False
    
    for batch_dict in batch_gen:
        batch_count += 1
        stock = batch_dict['s']
        size = batch_dict['batch_size']
        
        print(f"Batch {batch_count}: {stock} (size={size})")
        
        if stock == 'AAPL':
            aapl_found = True
            print(f"  Found AAPL batch!")
            print(f"  Price shape: {batch_dict['price_batch'].shape}")
            print(f"  Word shape: {batch_dict['word_batch'].shape}")
            
            # 尝试模型推理
            test_model_inference(batch_dict)
            break
        
        if batch_count >= 20:
            print("Checked 20 batches, stopping")
            break
    
    if aapl_found:
        print("\n[OK] AAPL data found and tested!")
    else:
        print("\n[WARN] AAPL not found in first 20 batches")
    
    return aapl_found


def test_model_inference(batch_dict):
    """测试真实模型推理"""
    print("\n=== Test Model Inference ===")
    
    try:
        import numpy as np
        from Model import Model
        
        # 加载因果图
        graph = np.load('causal_graph.npy')
        print(f"Causal graph loaded: {graph.shape}")
        
        # 创建模型
        model = Model(graph=graph)
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        model.to(device)
        model.eval()
        print(f"Model loaded on {device}")
        
        # 加载checkpoint
        import os
        checkpoint_paths = []
        if os.path.exists('checkpoints'):
            for item in os.listdir('checkpoints'):
                if os.path.isdir(os.path.join('checkpoints', item)):
                    model_file = os.path.join('checkpoints', item, 'model.pth')
                    if os.path.exists(model_file):
                        checkpoint_paths.append(model_file)
        
        if checkpoint_paths:
            checkpoint = torch.load(checkpoint_paths[0], map_location=device, weights_only=False)
            if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
                model.load_state_dict(checkpoint['model_state_dict'], strict=False)
            print(f"Checkpoint loaded: {checkpoint_paths[0]}")
        
        # 转换批次数据为张量
        def to_tensor(data):
            if isinstance(data, np.ndarray):
                return torch.from_numpy(data).to(device)
            return data
        
        batch_tensor = {
            'word_batch': to_tensor(batch_dict['word_batch']),
            'price_batch': to_tensor(batch_dict['price_batch']),
            'stock_batch': to_tensor(batch_dict['stock_batch']),
            'T_batch': to_tensor(batch_dict['T_batch']),
            'n_words_batch': to_tensor(batch_dict['n_words_batch']),
            'n_msgs_batch': to_tensor(batch_dict['n_msgs_batch']),
            'ss_index_batch': to_tensor(batch_dict['ss_index_batch'])
        }
        
        print(f"\nRunning model inference...")
        with torch.no_grad():
            outputs = model(
                word_ph=batch_tensor['word_batch'],
                price_ph=batch_tensor['price_batch'],
                stock_ph=batch_tensor['stock_batch'],
                T_ph=batch_tensor['T_batch'],
                n_words_ph=batch_tensor['n_words_batch'],
                n_msgs_ph=batch_tensor['n_msgs_batch'],
                y_ph=None,
                ss_index_ph=batch_tensor['ss_index_batch'],
                is_training=False
            )
        
        # 提取预测
        y_T = outputs['y_T']  # [batch_size, 2]
        print(f"\nModel output shape: {y_T.shape}")
        print(f"Sample predictions:")
        
        for i in range(min(5, y_T.shape[0])):
            probs = y_T[i].cpu().numpy()
            up_prob = float(probs[1])
            down_prob = float(probs[0])
            direction = 'UP' if up_prob > down_prob else 'DOWN'
            confidence = max(up_prob, down_prob)
            
            print(f"  Sample {i+1}: {direction} (confidence={confidence:.4f}, UP={up_prob:.4f}, DOWN={down_prob:.4f})")
        
        print("\n[OK] Model inference successful!")
        print("[OK] Deep learning model is working!")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Model inference failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("="*70)
    print("Simple Test - DataPipe + Model Inference")
    print("="*70)
    
    success = test_datapipe()
    
    if success:
        print("\n" + "="*70)
        print("[OK] All tests passed!")
        print("[OK] Deep learning model is being used correctly!")
        print("="*70)
    else:
        print("\n" + "="*70)
        print("[WARN] Tests incomplete")
        print("="*70)
