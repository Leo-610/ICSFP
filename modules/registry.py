from typing import Dict, Any
import torch
from .causal_module import StaticGraphCausalModule, DynamicCUTSPlusCausalModule
from .stocknet_module import StockNetModule
from .msgnet_module import MSGNetModule, MSGNetConfig


def build_modules(cfg: Dict[str, Any]):
    causal = None
    if cfg.get('causal', {}).get('enabled', False):
        if cfg['causal'].get('type', 'static') == 'static':
            graph = cfg['causal']['graph']  # torch.Tensor
            causal_dim = cfg['causal'].get('causal_dim')
            causal = StaticGraphCausalModule(graph_tensor=graph, causal_dim=causal_dim)
        else:
            cuts_cfg = cfg['causal'].get('cuts_cfg', {})
            top_k_scales = cfg['causal'].get('top_k_scales', 3)
            causal = DynamicCUTSPlusCausalModule(cuts_cfg=cuts_cfg, top_k_scales=top_k_scales)

    backbone_name = cfg['backbone']['name']
    if backbone_name.lower() == 'stocknet':
        graph = cfg.get('causal', {}).get('graph')
        backbone = StockNetModule(graph=graph)
    elif backbone_name.lower() == 'msgnet':
        m = cfg['backbone']['msgnet']
        msg_cfg = MSGNetConfig(
            enc_in=m['enc_in'], c_out=m['c_out'], seq_len=m['seq_len'], label_len=m['label_len'], pred_len=m['pred_len'],
            d_model=m.get('d_model', 64), d_ff=m.get('d_ff', 128), n_heads=m.get('n_heads', 4),
            e_layers=m.get('e_layers', 2), dropout=m.get('dropout', 0.2), embed=m.get('embed', 'timeF'),
            freq=m.get('freq', 'd'), top_k=m.get('top_k', 3), conv_channel=m.get('conv_channel', 16),
            skip_channel=m.get('skip_channel', 16), gcn_depth=m.get('gcn_depth', 2), propalpha=m.get('propalpha', 0.05),
            node_dim=m.get('node_dim', 16), individual=m.get('individual', True), task_name=m.get('task_name', 'classification')
        )
        backbone = MSGNetModule(msg_cfg)
    else:
        raise ValueError(f"Unknown backbone: {backbone_name}")

    return causal, backbone


