from typing import Optional
import torch
from .base import CausalModuleBase


class StaticGraphCausalModule(CausalModuleBase):
    def __init__(self, graph_tensor: torch.Tensor, causal_dim: Optional[int] = None):
        self.graph = graph_tensor.detach().float()
        self.num_nodes = self.graph.shape[0]
        self.causal_dim = causal_dim or self.num_nodes
        self.proj = None

    def compute_features(self, batch) -> torch.Tensor:
        stock_indices: torch.Tensor = batch['stock_ph']
        max_days: int = int(batch['max_days'])
        batch_size = stock_indices.shape[0]
        device = stock_indices.device
        clamped = torch.clamp(stock_indices, 0, self.num_nodes - 1)
        subgraph = self.graph[clamped][:, clamped]  # [B, B]
        feats = subgraph.unsqueeze(1).expand(-1, max_days, -1)  # [B, D, B]
        if feats.shape[-1] != self.causal_dim:
            if self.proj is None:
                self.proj = torch.nn.Linear(batch_size, self.causal_dim).to(device)
            feats = self.proj(feats)
        return feats


class DynamicCUTSPlusCausalModule(CausalModuleBase):
    def __init__(self, cuts_cfg: dict, top_k_scales: int = 3):
        # cuts_cfg should be compatible with your cuts_plus.main signature via opt
        self.cuts_cfg = cuts_cfg
        self.top_k_scales = top_k_scales

    def compute_features(self, batch) -> torch.Tensor:
        """
        Expect batch contains:
          - 'x_enc': [B, T, C] price window (float tensor)
          - 'stock_ph': [B] indices of stocks within window ordering (optional; if absent, assume first B assets)
          - 'max_days': int T
        Returns causal features [B, T, B] aggregated across top scales (mean).
        """
        import numpy as np
        import torch
        from multiscale_views import build_multiscale_views
        import cuts_plus
        from omegaconf import OmegaConf
        import os

        x_enc: torch.Tensor = batch['x_enc']  # [B, T, C]
        B, T, C = x_enc.shape
        # Use CPU numpy for CUTS+ to avoid cuda <-> python overhead
        X = x_enc.detach().to('cpu').numpy()  # [B, T, C]

        # Use the first sample's window to compute dynamic causal graph (fast & deterministic)
        X_tc = X[0]

        # Build multiscale narrow-band views
        views_out = build_multiscale_views(
            X_tc, top_k=self.top_k_scales, preproc='log_return', standardize=True, post_standardize=True
        )
        views = views_out['views']

        graphs = []
        mask = np.ones_like(X_tc, dtype=bool)  # no missing mask
        for _, Xs in views.items():
            # Run CUTS+ per scale; you may adapt the call if your signature differs
            try:
                opt = self.cuts_cfg
                # If a dict or empty provided, load a default OPT config
                if isinstance(opt, dict) or opt is None:
                    # try local opt path first, then submodule
                    candidate_paths = [
                        os.path.join(os.getcwd(), 'opt', 'lorenz_example.yaml'),
                        os.path.join(os.getcwd(), 'CUTS_Plus', 'opt', 'lorenz_example.yaml'),
                    ]
                    opt_path = next((p for p in candidate_paths if os.path.exists(p)), None)
                    if opt_path is None:
                        raise FileNotFoundError('Default CUTS+ opt yaml not found')
                    opt = OmegaConf.load(opt_path)
                g = cuts_plus.main(Xs, mask, None, opt, None, device='cpu')
            except TypeError:
                # Alternate signature used in repo wrappers
                g = cuts_plus.main(opt)
            # Ensure square matrix CxC
            g = np.asarray(g)
            if g.ndim == 2 and g.shape[0] == g.shape[1] == C:
                graphs.append(g)

        if len(graphs) == 0:
            g_agg = np.zeros((C, C), dtype=np.float32)
        else:
            g_agg = np.mean(graphs, axis=0)

        # Map to batch-wise features [B, T, B] by selecting rows/cols per batch order
        # Here we assume the first B assets correspond to batch positions 0..B-1
        sub = g_agg[:B, :B]
        feats = np.repeat(sub[None, :, :], T, axis=0)  # [T, B, B]
        feats = np.transpose(feats, (1, 0, 2))         # [B, T, B]
        return torch.tensor(feats, dtype=x_enc.dtype, device=x_enc.device)


