#!/usr/bin/env python3
import os
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from torch.distributions import Normal, kl_divergence
from ConfigLoader import logger, ss_size, vocab_size, config_model, path_parser


class Model(nn.Module):
    def __init__(self, graph=None):
        super(Model, self).__init__()
        logger.info('INIT: #stock: {0}, #vocab+1: {1}'.format(ss_size, vocab_size))

        # 因果图 - 新增
        self.graph = torch.tensor(graph, dtype=torch.float32) if graph is not None else None
        self.n_stocks = graph.shape[0] if graph is not None else ss_size

        # model config (保持原有配置)
        self.mode = config_model['mode']
        self.opt = config_model['opt']
        self.lr = config_model['lr']
        self.decay_step = config_model['decay_step']
        self.decay_rate = config_model['decay_rate']
        self.momentum = config_model['momentum']

        self.kl_lambda_anneal_rate = config_model['kl_lambda_anneal_rate']
        self.kl_lambda_start_step = config_model['kl_lambda_start_step']
        self.use_constant_kl_lambda = config_model['use_constant_kl_lambda']
        self.constant_kl_lambda = config_model['constant_kl_lambda']

        self.daily_att = config_model['daily_att']
        self.alpha = config_model['alpha']

        self.clip = config_model['clip']
        self.n_epochs = config_model['n_epochs']
        self.batch_size_for_name = config_model['batch_size']

        self.max_n_days = config_model['max_n_days']
        self.max_n_msgs = config_model['max_n_msgs']
        self.max_n_words = config_model['max_n_words']

        self.weight_init = config_model['weight_init']
        self.word_embed_type = config_model['word_embed_type']

        self.y_size = config_model['y_size']
        self.word_embed_size = config_model['word_embed_size']
        self.stock_embed_size = config_model['stock_embed_size']
        self.price_embed_size = config_model['word_embed_size']

        self.mel_cell_type = config_model['mel_cell_type']
        self.variant_type = config_model['variant_type']
        self.vmd_cell_type = config_model['vmd_cell_type']
        self.vmd_rec = config_model['vmd_rec']

        self.mel_h_size = config_model['mel_h_size']
        self.msg_embed_size = config_model['mel_h_size']
        self.corpus_embed_size = config_model['mel_h_size']

        self.h_size = config_model['h_size']
        self.z_size = config_model['h_size']
        self.g_size = config_model['g_size']
        self.use_in_bn = config_model['use_in_bn']
        self.use_o_bn = config_model['use_o_bn']
        self.use_g_bn = config_model['use_g_bn']

        self.dropout_train_mel_in = config_model['dropout_mel_in']
        self.dropout_train_mel = config_model['dropout_mel']
        self.dropout_train_ce = config_model['dropout_ce']
        self.dropout_train_vmd_in = config_model['dropout_vmd_in']
        self.dropout_train_vmd = config_model['dropout_vmd']

        # Global step counter
        self.global_step = 0

        # 模型名称生成 (保持原有逻辑)
        name_pattern_max_n = 'days-{0}.msgs-{1}-words-{2}'
        name_max_n = name_pattern_max_n.format(self.max_n_days, self.max_n_msgs, self.max_n_words)

        name_pattern_input_type = 'word_embed-{0}.vmd_in-{1}'
        name_input_type = name_pattern_input_type.format(self.word_embed_type, self.variant_type)

        name_pattern_key = 'alpha-{0}.anneal-{1}.rec-{2}'
        name_key = name_pattern_key.format(self.alpha, self.kl_lambda_anneal_rate, self.vmd_rec)

        name_pattern_train = 'batch-{0}.opt-{1}.lr-{2}-drop-{3}-cell-{4}'
        name_train = name_pattern_train.format(self.batch_size_for_name, self.opt, self.lr,
                                               self.dropout_train_mel_in, self.mel_cell_type)

        name_tuple = (self.mode, name_max_n, name_input_type, name_key, name_train)
        self.model_name = '_'.join(name_tuple)

        # 路径配置 (保持原有)
        self.tf_graph_path = os.path.join(path_parser.graphs, self.model_name)
        self.tf_checkpoints_path = os.path.join(path_parser.checkpoints, self.model_name)
        self.tf_checkpoint_file_path = os.path.join(self.tf_checkpoints_path, 'checkpoint')
        self.tf_saver_path = os.path.join(self.tf_checkpoints_path, 'sess')

        # 初始化神经网络层
        self._build_layers()

    def _build_layers(self):
        """构建所有神经网络层"""

        # 1. 词嵌入层
        self.word_embedding = nn.Embedding(vocab_size, self.word_embed_size)

        # 2. 消息嵌入层 (MEL)
        if self.mel_cell_type == 'gru':
            self.mel_cell_f = nn.GRU(self.word_embed_size, self.mel_h_size, batch_first=True)
            self.mel_cell_b = nn.GRU(self.word_embed_size, self.mel_h_size, batch_first=True)
        elif self.mel_cell_type == 'lstm':
            self.mel_cell_f = nn.LSTM(self.word_embed_size, self.mel_h_size, batch_first=True)
            self.mel_cell_b = nn.LSTM(self.word_embed_size, self.mel_h_size, batch_first=True)
        else:
            self.mel_cell_f = nn.RNN(self.word_embed_size, self.mel_h_size, batch_first=True)
            self.mel_cell_b = nn.RNN(self.word_embed_size, self.mel_h_size, batch_first=True)

        # 3. 语料嵌入注意力层
        self.corpus_attention = nn.Linear(self.msg_embed_size, self.msg_embed_size)
        self.corpus_attention_weight = nn.Linear(self.msg_embed_size, 1)

        # 4. 变分运动解码器 (VMD)
        if self.vmd_cell_type == 'gru':
            self.vmd_cell = nn.GRU(self.corpus_embed_size + 3, self.h_size, batch_first=True)
        else:
            self.vmd_cell = nn.LSTM(self.corpus_embed_size + 3, self.h_size, batch_first=True)

        # 5. 变分推理层
        self.h_z_prior = nn.Linear(self.corpus_embed_size + 3 + self.h_size + self.z_size, self.z_size)
        self.h_z_post = nn.Linear(self.corpus_embed_size + 3 + self.h_size + self.y_size + self.z_size, self.z_size)

        self.z_prior_mean = nn.Linear(self.z_size, self.z_size)
        self.z_prior_logvar = nn.Linear(self.z_size, self.z_size)
        self.z_post_mean = nn.Linear(self.z_size, self.z_size)
        self.z_post_logvar = nn.Linear(self.z_size, self.z_size)

        # 6. 生成层
        self.g_layer = nn.Linear(self.h_size + self.z_size, self.g_size)
        self.y_layer = nn.Linear(self.g_size, self.y_size)

        # 7. 时序注意力层
        self.temporal_att_proj_i = nn.Linear(self.g_size, self.g_size)
        self.temporal_att_w_i = nn.Linear(self.g_size, 1)
        self.temporal_att_proj_d = nn.Linear(self.g_size, self.g_size)

        # 8. 因果图神经网络层 - 新增
        if self.graph is not None:
            self.causal_w1 = nn.ModuleList([
                nn.Linear(self.z_size, self.z_size) for _ in range(self.max_n_days)
            ])
            self.causal_w2 = nn.ModuleList([
                nn.Linear(self.z_size, self.z_size) for _ in range(self.max_n_days)
            ])
            # 因果变量维度
            self.causal_z_size = self.z_size

        # 9. 最终融合预测层 - 修改
        if self.graph is not None:
            # E (文本) + S (价格) + Z (因果变量)
            final_input_size = self.corpus_embed_size + 3 + self.causal_z_size
        else:
            final_input_size = self.g_size + self.g_size  # 原有的融合方式

        self.final_prediction = nn.Linear(final_input_size, self.y_size)

        # Dropout层
        self.dropout_mel_in = nn.Dropout(self.dropout_train_mel_in)
        self.dropout_mel = nn.Dropout(self.dropout_train_mel)
        self.dropout_ce = nn.Dropout(self.dropout_train_ce)
        self.dropout_vmd_in = nn.Dropout(self.dropout_train_vmd_in)
        self.dropout_vmd = nn.Dropout(self.dropout_train_vmd)

    def init_word_table(self, word_table_init):
        """初始化词向量表"""
        self.word_embedding.weight.data.copy_(torch.from_numpy(word_table_init))
        self.word_embedding.weight.requires_grad = False  # 冻结词向量

    def _create_msg_embed_layer(self, word_embed, ss_index_ph, n_words_ph):
        """消息嵌入层"""
        batch_size, max_days, max_msgs, max_words, embed_size = word_embed.shape

        # 重塑为二维进行RNN处理
        word_embed_flat = word_embed.view(batch_size * max_days * max_msgs, max_words, embed_size)
        n_words_flat = n_words_ph.view(-1)

        # 创建序列长度掩码
        lengths = n_words_flat.clamp(min=1)  # 避免长度为0

        # 双向RNN处理
        # 前向
        packed_input = nn.utils.rnn.pack_padded_sequence(
            word_embed_flat, lengths.cpu(), batch_first=True, enforce_sorted=False
        )
        packed_output_f, _ = self.mel_cell_f(packed_input)
        output_f, _ = nn.utils.rnn.pad_packed_sequence(packed_output_f, batch_first=True)

        # 后向 (翻转序列)
        word_embed_reversed = torch.flip(word_embed_flat, dims=[1])
        packed_input_b = nn.utils.rnn.pack_padded_sequence(
            word_embed_reversed, lengths.cpu(), batch_first=True, enforce_sorted=False
        )
        packed_output_b, _ = self.mel_cell_b(packed_input_b)
        output_b, _ = nn.utils.rnn.pad_packed_sequence(packed_output_b, batch_first=True)
        output_b = torch.flip(output_b, dims=[1])  # 翻转回来

        # 提取股票符号位置的表示
        ss_index_flat = ss_index_ph.view(-1)
        batch_indices = torch.arange(batch_size * max_days * max_msgs).to(word_embed.device)

        # 安全索引，避免越界
        ss_index_clamped = ss_index_flat.clamp(0, max_words - 1)

        msg_embed_f = output_f[batch_indices, ss_index_clamped]
        msg_embed_b = output_b[batch_indices, ss_index_clamped]

        # 融合前向和后向
        msg_embed = (msg_embed_f + msg_embed_b) / 2

        # 重塑回原始形状
        msg_embed = msg_embed.view(batch_size, max_days, max_msgs, self.msg_embed_size)

        return self.dropout_mel(msg_embed)

    def _create_corpus_embed(self, msg_embed, n_msgs_ph):
        """语料嵌入层 - 注意力聚合"""
        batch_size, max_days, max_msgs, msg_embed_size = msg_embed.shape

        # 计算注意力分数
        proj_u = torch.tanh(self.corpus_attention(msg_embed))
        u = self.corpus_attention_weight(proj_u).squeeze(-1)  # [batch, days, msgs]

        # 创建消息掩码
        msg_mask = torch.arange(max_msgs).unsqueeze(0).unsqueeze(0).to(msg_embed.device)
        msg_mask = msg_mask < n_msgs_ph.unsqueeze(-1)

        # 应用掩码
        u_masked = u.masked_fill(~msg_mask, float('-inf'))
        attention_weights = F.softmax(u_masked, dim=-1)
        attention_weights = torch.nan_to_num(attention_weights, 0.0)

        # 加权聚合
        corpus_embed = torch.bmm(
            attention_weights.view(batch_size * max_days, 1, max_msgs),
            msg_embed.view(batch_size * max_days, max_msgs, msg_embed_size)
        ).view(batch_size, max_days, msg_embed_size)

        return self.dropout_ce(corpus_embed)

    def _create_causal_variables(self, batch_size, stock_batch, device):
        """
        生成因果变量
        Z_i^{(t)} = σ(W1^{(t)} Z_i^{(t-1)} + W2^{(t)} σ(Σ_j c_{ji} · Z_j^{(t-1)}))
        """
        if self.graph is None:
            return None

        # 初始化因果变量 [batch_size, max_days, causal_z_size]
        causal_Z = torch.zeros(batch_size, self.max_n_days, self.causal_z_size).to(device)

        # 初始化 Z^{(0)}
        causal_Z[:, 0, :] = torch.randn(batch_size, self.causal_z_size).to(device)

        stock_batch_cpu = stock_batch.cpu()
        graph_batch = self.graph[stock_batch_cpu][:, stock_batch_cpu].to(device)

        # 时序递推生成因果变量
        for t in range(1, self.max_n_days):
            Z_prev = causal_Z[:, t-1, :]  # [batch_size, causal_z_size]

            # 第一项: W1^{(t)} Z_i^{(t-1)}
            term1 = self.causal_w1[t](Z_prev)  # [batch_size, causal_z_size]

            # 第二项: W2^{(t)} σ(Σ_j c_{ji} · Z_j^{(t-1)})
            # 因果图加权聚合: c_{ji} · Z_j^{(t-1)}
            causal_influence = torch.matmul(graph_batch, Z_prev)  # [batch_size, causal_z_size]
            causal_influence_activated = torch.sigmoid(causal_influence)
            term2 = self.causal_w2[t](causal_influence_activated)

            # 组合并激活
            causal_Z[:, t, :] = torch.sigmoid(term1 + term2)

        return causal_Z

    def _vmd_with_zh_rec(self, x, T_ph, y_ph, batch_size, device):
        """变分运动解码器 - zh递归版本"""
        # RNN处理时序
        h_s, _ = self.vmd_cell(x)  # [batch_size, max_days, h_size]

        # 初始化变分变量
        z_prior_list = []
        z_post_list = []
        kl_list = []

        z_post_prev = torch.randn(batch_size, self.z_size).to(device)

        for t in range(self.max_n_days):
            x_t = x[:, t, :]  # [batch_size, input_size]
            h_t = h_s[:, t, :]  # [batch_size, h_size]

            # 先验分布 p(z_t | x_≤t, h_t, z_{t-1})
            h_z_prior_input = torch.cat([x_t, h_t, z_post_prev], dim=-1)
            h_z_prior_t = torch.tanh(self.h_z_prior(h_z_prior_input))

            z_prior_mean = self.z_prior_mean(h_z_prior_t)
            z_prior_logvar = self.z_prior_logvar(h_z_prior_t)
            z_prior_std = torch.exp(0.5 * z_prior_logvar)

            z_prior_dist = Normal(z_prior_mean, z_prior_std)
            z_prior_t = z_prior_dist.rsample()

            # 后验分布 q(z_t | x_≤t, h_t, y_t, z_{t-1})
            if t < y_ph.shape[1]:
                y_t = y_ph[:, t, :]  # [batch_size, y_size]
                h_z_post_input = torch.cat([x_t, h_t, y_t, z_post_prev], dim=-1)
            else:
                # 超出标签范围，使用零填充
                y_t = torch.zeros(batch_size, self.y_size).to(device)
                h_z_post_input = torch.cat([x_t, h_t, y_t, z_post_prev], dim=-1)

            h_z_post_t = torch.tanh(self.h_z_post(h_z_post_input))

            z_post_mean = self.z_post_mean(h_z_post_t)
            z_post_logvar = self.z_post_logvar(h_z_post_t)
            z_post_std = torch.exp(0.5 * z_post_logvar)

            z_post_dist = Normal(z_post_mean, z_post_std)
            z_post_t = z_post_dist.rsample()

            # KL散度
            kl_t = kl_divergence(z_post_dist, z_prior_dist)

            z_prior_list.append(z_prior_t)
            z_post_list.append(z_post_t)
            kl_list.append(kl_t)

            z_post_prev = z_post_t

        z_prior = torch.stack(z_prior_list, dim=1)  # [batch_size, max_days, z_size]
        z_post = torch.stack(z_post_list, dim=1)
        kl = torch.stack(kl_list, dim=1)  # [batch_size, max_days, z_size]

        # 生成g和y
        g = torch.tanh(self.g_layer(torch.cat([h_s, z_post], dim=-1)))  # [batch_size, max_days, g_size]
        y = F.softmax(self.y_layer(g), dim=-1)  # [batch_size, max_days, y_size]

        return g, y, kl.sum(dim=-1), z_post, z_prior  # kl: [batch_size, max_days]

    def _build_temporal_att(self, g, g_T, mask_aux_trading_days):
        """时序注意力机制"""
        batch_size = g.shape[0]

        # 计算注意力分数
        proj_i = torch.tanh(self.temporal_att_proj_i(g))
        v_i = self.temporal_att_w_i(proj_i).squeeze(-1)  # [batch_size, max_days]

        proj_d = torch.tanh(self.temporal_att_proj_d(g))
        g_T_expanded = g_T.unsqueeze(1)  # [batch_size, 1, g_size]
        v_d = torch.bmm(proj_d, g_T_expanded.transpose(-1, -2)).squeeze(-1)  # [batch_size, max_days]

        # 融合注意力分数
        aux_score = v_i * v_d

        # 应用掩码
        aux_score_masked = aux_score.masked_fill(~mask_aux_trading_days, float('-inf'))
        v_stared = F.softmax(aux_score_masked, dim=-1)
        v_stared = torch.nan_to_num(v_stared, 0.0)

        return v_stared

    def forward(self, word_ph, price_ph, stock_ph, T_ph, n_words_ph, n_msgs_ph,
                y_ph=None, ss_index_ph=None, is_training=True):
        """前向传播"""
        batch_size = word_ph.shape[0]
        device = word_ph.device

        # 1. 词嵌入
        word_embed = self.word_embedding(word_ph)
        if self.use_in_bn and is_training:
            # 可以添加BatchNorm，这里简化
            pass
        word_embed = self.dropout_mel_in(word_embed) if is_training else word_embed

        # 2. 消息嵌入层
        if self.variant_type != 'tech':
            msg_embed = self._create_msg_embed_layer(word_embed, ss_index_ph, n_words_ph)

            # 3. 语料嵌入
            corpus_embed = self._create_corpus_embed(msg_embed, n_msgs_ph)

        # 4. 市场信息编码
        if self.variant_type == 'tech':
            x = price_ph  # 仅价格
        elif self.variant_type == 'fund':
            x = corpus_embed  # 仅文本
        else:  # hedge
            x = torch.cat([corpus_embed, price_ph], dim=-1)  # 文本+价格

        x = self.dropout_vmd_in(x) if is_training else x

        # 5. 变分运动解码器
        if y_ph is not None:
            g, y, kl, z_post, z_prior = self._vmd_with_zh_rec(x, T_ph, y_ph, batch_size, device)
        else:
            # 推理模式，使用零标签
            y_dummy = torch.zeros(batch_size, self.max_n_days, self.y_size).to(device)
            g, y, kl, z_post, z_prior = self._vmd_with_zh_rec(x, T_ph, y_dummy, batch_size, device)

        # 6. 提取目标日信息
        batch_indices = torch.arange(batch_size).to(device)
        T_indices = (T_ph - 1).clamp(0, self.max_n_days - 1)
        g_T = g[batch_indices, T_indices]  # [batch_size, g_size]

        # 7. 时序注意力
        mask_aux_trading_days = torch.arange(self.max_n_days).unsqueeze(0).to(device) < (T_ph - 1).unsqueeze(1)
        v_stared = self._build_temporal_att(g, g_T, mask_aux_trading_days)

        # 8. 生成因果变量 - 新增
        causal_Z = self._create_causal_variables(batch_size, stock_ph, device)

        # 9. 融合预测 - 修改
        if causal_Z is not None:
            # 提取目标日的因果变量
            causal_Z_T = causal_Z[batch_indices, T_indices]  # [batch_size, causal_z_size]

            # 提取目标日的文本和价格特征
            E_T = corpus_embed[batch_indices, T_indices] if self.variant_type != 'tech' else torch.zeros(batch_size, self.corpus_embed_size).to(device)
            S_T = price_ph[batch_indices, T_indices]  # [batch_size, 3]

            # 按照公式融合: ŷ = softmax(W_y [E; S; Z] + b_y)
            fused_features = torch.cat([E_T, S_T, causal_Z_T], dim=-1)
            y_T = F.softmax(self.final_prediction(fused_features), dim=-1)
        else:
            # 原有的注意力加权方式
            if self.daily_att == 'y':
                context = y.transpose(1, 2)  # [batch_size, y_size, max_days]
            else:
                context = g.transpose(1, 2)  # [batch_size, g_size, max_days]

            att_c = torch.bmm(context, v_stared.unsqueeze(-1)).squeeze(-1)  # [batch_size, context_size]
            fused_features = torch.cat([att_c, g_T], dim=-1)
            y_T = F.softmax(self.final_prediction(fused_features), dim=-1)

        # 10. 提取目标标签 (如果提供)
        if y_ph is not None:
            y_T_ = y_ph[batch_indices, T_indices]
        else:
            y_T_ = None

        return {
            'y_T': y_T,
            'y_T_': y_T_,
            'y': y,
            'g': g,
            'kl': kl,
            'v_stared': v_stared,
            'causal_Z': causal_Z,  # 新增输出
            'corpus_embed': corpus_embed if self.variant_type != 'tech' else None,
            'price_features': price_ph,
        }

    def compute_loss(self, outputs, T_ph, alpha=None):
        """计算损失函数"""
        y_T = outputs['y_T']
        y_T_ = outputs['y_T_']
        y = outputs['y']
        kl = outputs['kl']
        v_stared = outputs['v_stared']

        if y_T_ is None:
            return torch.tensor(0.0)

        batch_size = y_T.shape[0]
        device = y_T.device

        # 目标日损失
        eps = 1e-8
        likelihood_T = torch.sum(y_T_ * torch.log(y_T + eps), dim=-1)  # [batch_size]

        # 辅助日损失
        batch_indices = torch.arange(batch_size).to(device)
        T_indices = (T_ph - 1).clamp(0, self.max_n_days - 1)

        # 创建辅助日掩码
        aux_mask = torch.arange(self.max_n_days).unsqueeze(0).to(device) < T_indices.unsqueeze(1)

        # 计算辅助日似然
        likelihood_aux = torch.sum(outputs['y_T_'].unsqueeze(1) * torch.log(y + eps), dim=-1)  # [batch_size, max_days]
        likelihood_aux = likelihood_aux * aux_mask.float()

        # KL散度损失
        kl_lambda = self._kl_lambda()
        kl_loss_T = kl[batch_indices, T_indices]
        kl_loss_aux = kl * aux_mask.float()

        # 变分下界
        if alpha is None:
            alpha = self.alpha

        # 辅助日的注意力权重
        v_aux = alpha * v_stared  # [batch_size, max_days]

        # 目标日变分下界
        obj_T = likelihood_T - kl_lambda * kl_loss_T

        # 辅助日变分下界
        obj_aux = likelihood_aux - kl_lambda * kl_loss_aux  # [batch_size, max_days]
        obj_aux_weighted = torch.sum(obj_aux * v_aux, dim=1)  # [batch_size]

        # 总变分下界
        obj = obj_T + obj_aux_weighted
        loss = -torch.mean(obj)

        return loss

    def _kl_lambda(self):
        """KL散度退火系数"""
        if self.use_constant_kl_lambda:
            return self.constant_kl_lambda
        else:
            if self.global_step < self.kl_lambda_start_step:
                return 0.0
            else:
                return min(self.kl_lambda_anneal_rate * self.global_step, 1.0)

    def step_global_step(self):
        """增加全局步数"""
        self.global_step += 1