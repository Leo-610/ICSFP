from typing import Any, Dict
import torch
import torch.nn.functional as F
from .base import BackboneModuleBase
from Model import Model as StockNetModel


class StockNetModule(BackboneModuleBase):
    def __init__(self, graph: torch.Tensor = None):
        self.model = StockNetModel(graph=graph)

    def forward(self, inputs: Dict[str, Any]) -> Dict[str, torch.Tensor]:
        outputs = self.model(
            word_ph=inputs['word_ph'],
            price_ph=inputs['price_ph'],
            stock_ph=inputs['stock_ph'],
            T_ph=inputs['T_ph'],
            n_words_ph=inputs['n_words_ph'],
            n_msgs_ph=inputs['n_msgs_ph'],
            y_ph=inputs.get('y_ph'),
            ss_index_ph=inputs.get('ss_index_ph'),
            is_training=inputs.get('is_training', True),
        )
        logits = torch.log(torch.clamp(outputs['y_T'], min=1e-8))
        return {'probs': outputs['y_T'], 'logits': logits}


