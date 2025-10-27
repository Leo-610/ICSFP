from typing import Any, Dict
import torch
from .base import BackboneModuleBase


class MSGNetConfig:
    def __init__(self, enc_in: int, c_out: int, seq_len: int, label_len: int, pred_len: int,
                 d_model: int = 64, d_ff: int = 128, n_heads: int = 4, e_layers: int = 2,
                 dropout: float = 0.2, embed: str = 'timeF', freq: str = 'd', top_k: int = 3,
                 conv_channel: int = 16, skip_channel: int = 16, gcn_depth: int = 2,
                 propalpha: float = 0.05, node_dim: int = 16, individual: bool = True,
                 task_name: str = 'classification'):
        self.enc_in = enc_in
        self.c_out = c_out
        self.seq_len = seq_len
        self.label_len = label_len
        self.pred_len = pred_len
        self.d_model = d_model
        self.d_ff = d_ff
        self.n_heads = n_heads
        self.e_layers = e_layers
        self.dropout = dropout
        self.embed = embed
        self.freq = freq
        self.top_k = top_k
        self.conv_channel = conv_channel
        self.skip_channel = skip_channel
        self.gcn_depth = gcn_depth
        self.propalpha = propalpha
        self.node_dim = node_dim
        self.individual = individual
        self.task_name = task_name


class MSGNetModule(BackboneModuleBase):
    def __init__(self, configs: MSGNetConfig):
        from MSGNet.models.MSGNet import Model as MSGNetModel
        self.configs = configs
        self.model = MSGNetModel(configs)

        # Projection to class logits if needed
        self.classifier = torch.nn.Linear(configs.c_out, configs.c_out)

    def forward(self, inputs: Dict[str, Any]) -> Dict[str, torch.Tensor]:
        x_enc = inputs['x_enc']  # [B, T, C]
        x_mark_enc = inputs.get('x_mark_enc')  # [B, T, F_time]
        # MSGNet needs x_dec, x_mark_dec; we can pass zeros for classification-like usage
        B, T, C = x_enc.shape
        pred_len = self.configs.pred_len
        x_dec = torch.zeros(B, pred_len, C, device=x_enc.device, dtype=x_enc.dtype)
        x_mark_dec = torch.zeros_like(x_dec)

        preds = self.model(x_enc, x_mark_enc, x_dec, x_mark_dec)  # [B, pred_len, C]

        # Use the last step prediction as features
        last_pred = preds[:, -1, :]  # [B, C]
        logits = self.classifier(last_pred)
        probs = torch.softmax(logits, dim=-1)
        return {'probs': probs, 'logits': logits, 'pred_seq': preds}


