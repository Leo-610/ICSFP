import abc
from typing import Any, Dict, Optional, Tuple
import torch


class CausalModuleBase(abc.ABC):
    @abc.abstractmethod
    def compute_features(self, batch: Dict[str, Any]) -> torch.Tensor:
        """
        Compute time-aligned causal features based on current batch context.
        Expected shape: [batch_size, max_days, causal_dim]
        Required batch keys depend on implementation (e.g., x_enc, stock_ph, max_days).
        """
        raise NotImplementedError


class BackboneModuleBase(abc.ABC):
    @abc.abstractmethod
    def forward(self, inputs: Dict[str, Any]) -> Dict[str, torch.Tensor]:
        """
        Run forward pass given a dict of inputs. Returns a dict with at least 'logits' or 'probs'.
        """
        raise NotImplementedError


def move_to_device(batch: Dict[str, Any], device: torch.device) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k, v in batch.items():
        if isinstance(v, torch.Tensor):
            out[k] = v.to(device)
        else:
            out[k] = v
    return out


