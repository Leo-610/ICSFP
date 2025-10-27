from typing import Dict, Any, Optional
import torch
from modules.base import move_to_device


class ForecastPipeline:
    def __init__(self, causal_module=None, backbone_module=None, device: Optional[torch.device] = None):
        self.causal_module = causal_module
        self.backbone_module = backbone_module
        self.device = device or (torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu'))

    def forward(self, batch: Dict[str, Any]) -> Dict[str, torch.Tensor]:
        batch = move_to_device(batch, self.device)

        if self.causal_module is not None:
            causal_feats = self.causal_module.compute_features(batch)
            batch['causal_feats'] = causal_feats

        outputs = self.backbone_module.forward(batch)
        return outputs


