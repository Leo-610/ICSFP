#!/usr/bin/env python3
import os
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import metrics as metrics
import stat_logger as stat_logger
from DataPipe import DataPipe
from ConfigLoader import logger


class Executor:
    def __init__(self, model, silence_step=200, skip_step=20, device='cuda'):
        self.model = model
        self.silence_step = silence_step
        self.skip_step = skip_step
        self.pipe = DataPipe()
        self.device = device

        # 将模型移动到指定设备
        self.model.to(self.device)

        # 初始化优化器
        self._setup_optimizer()

    def _setup_optimizer(self):
        """设置优化器"""
        if self.model.opt == 'sgd':
            self.optimizer = optim.SGD(
                self.model.parameters(),
                lr=self.model.lr,
                momentum=self.model.momentum
            )
            # 学习率调度器
            self.scheduler = optim.lr_scheduler.ExponentialLR(
                self.optimizer,
                gamma=self.model.decay_rate
            )
        else:  # adam
            self.optimizer = optim.Adam(
                self.model.parameters(),
                lr=self.model.lr
            )
            self.scheduler = None

    def _to_tensor(self, batch_dict):
        """将numpy数组转换为PyTorch张量并移动到设备（字符串数组原样保留）"""
        tensor_dict = {}
        for key, value in batch_dict.items():
            if isinstance(value, np.ndarray) and np.issubdtype(value.dtype, np.number):
                tensor_dict[key] = torch.from_numpy(value).to(self.device)
            else:
                tensor_dict[key] = value
        return tensor_dict

    def unit_test_train(self):
        """单元测试训练"""
        # 初始化词向量表
        word_table_init = self.pipe.init_word_table()
        self.model.init_word_table(word_table_init)
        logger.info('Word table init: done!')

        logger.info('Model: {0}, start a new session!'.format(self.model.model_name))

        n_iter = 0
        train_batch_loss_list = []
        train_epoch_size = 0.0
        train_epoch_n_acc = 0.0

        # 获取训练数据生成器
        train_batch_gen = self.pipe.batch_gen(phase='train')
        train_batch_dict = next(train_batch_gen)
        train_batch_dict = self._to_tensor(train_batch_dict)

        self.model.train()

        while n_iter < 100:
            self.optimizer.zero_grad()

            # 前向传播
            outputs = self.model(
                word_ph=train_batch_dict['word_batch'],
                price_ph=train_batch_dict['price_batch'],
                stock_ph=train_batch_dict['stock_batch'],
                T_ph=train_batch_dict['T_batch'],
                n_words_ph=train_batch_dict['n_words_batch'],
                n_msgs_ph=train_batch_dict['n_msgs_batch'],
                y_ph=train_batch_dict['y_batch'],
                ss_index_ph=train_batch_dict['ss_index_batch'],
                is_training=True
            )

            # 计算损失
            loss = self.model.compute_loss(outputs, train_batch_dict['T_batch'])

            # 反向传播
            loss.backward()

            # 梯度裁剪
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.model.clip)

            # 优化步骤
            self.optimizer.step()
            self.model.step_global_step()

            # 计算准确率
            train_batch_y = outputs['y_T'].detach().cpu().numpy()
            train_batch_y_ = outputs['y_T_'].detach().cpu().numpy()
            train_batch_loss = loss.item()

            # 统计
            train_epoch_size += float(train_batch_dict['batch_size'])
            train_batch_loss_list.append(train_batch_loss)
            train_batch_n_acc = metrics.n_accurate_numpy(train_batch_y, train_batch_y_)
            train_epoch_n_acc += float(train_batch_n_acc)

            stat_logger.print_batch_stat(
                n_iter, train_batch_loss, train_batch_n_acc, train_batch_dict['batch_size']
            )
            n_iter += 1

    def generation(self, phase, use_mcc=False):
        """验证/测试阶段的生成"""
        self.model.eval()

        generation_gen = self.pipe.batch_gen_by_stocks(phase)

        gen_loss_list = []
        gen_size, gen_n_acc = 0.0, 0.0
        y_list, y_list_ = [], []

        with torch.no_grad():
            for gen_batch_dict in generation_gen:
                gen_batch_dict = self._to_tensor(gen_batch_dict)

                # 前向传播
                outputs = self.model(
                    word_ph=gen_batch_dict['word_batch'],
                    price_ph=gen_batch_dict['price_batch'],
                    stock_ph=gen_batch_dict['stock_batch'],
                    T_ph=gen_batch_dict['T_batch'],
                    n_words_ph=gen_batch_dict['n_words_batch'],
                    n_msgs_ph=gen_batch_dict['n_msgs_batch'],
                    y_ph=gen_batch_dict['y_batch'],
                    ss_index_ph=gen_batch_dict['ss_index_batch'],
                    is_training=False
                )

                # 计算损失
                gen_batch_loss = self.model.compute_loss(outputs, gen_batch_dict['T_batch'])

                # 获取结果
                gen_batch_y = outputs['y_T'].cpu().numpy()
                gen_batch_y_ = outputs['y_T_'].cpu().numpy()

                # 收集结果
                y_list.append(gen_batch_y)
                y_list_.append(gen_batch_y_)
                gen_loss_list.append(gen_batch_loss.item())

                gen_batch_n_acc = float(metrics.n_accurate_numpy(gen_batch_y, gen_batch_y_))
                gen_n_acc += gen_batch_n_acc

                batch_size = float(gen_batch_dict['batch_size'])
                gen_size += batch_size

        results = metrics.eval_res(gen_n_acc, gen_size, gen_loss_list, y_list, y_list_, use_mcc=use_mcc)
        return results

    def train_and_dev(self):
        """训练和验证主循环"""
        # 初始化词向量表
        word_table_init = self.pipe.init_word_table()
        self.model.init_word_table(word_table_init)
        logger.info('Word table init: done!')

        # 检查点恢复
        checkpoint_path = os.path.join(self.model.tf_checkpoints_path, 'model.pth')
        start_epoch = 0

        if os.path.exists(checkpoint_path):
            try:
                checkpoint = torch.load(checkpoint_path, map_location=self.device, weights_only=False)
                # 使用 strict=False 来兼容不同版本的模型
                missing, unexpected = self.model.load_state_dict(checkpoint['model_state_dict'], strict=False)
                if missing:
                    logger.warning(f'Missing keys in checkpoint: {missing}')
                if unexpected:
                    logger.warning(f'Unexpected keys in checkpoint (ignored): {unexpected}')
                self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
                start_epoch = checkpoint['epoch']
                self.model.global_step = checkpoint['global_step']
                logger.info('Model: {0}, session restored from epoch {1}!'.format(
                    self.model.model_name, start_epoch))
            except Exception as e:
                logger.warning(f'Failed to load checkpoint: {e}')
                logger.info('Starting fresh training...')
                start_epoch = 0
        else:
            logger.info('Model: {0}, start a new session!'.format(self.model.model_name))

        # 训练循环
        for epoch in range(start_epoch, self.model.n_epochs):
            logger.info('Epoch: {0}/{1} start'.format(epoch + 1, self.model.n_epochs))

            # 训练阶段
            self.model.train()
            train_batch_loss_list = []
            epoch_size, epoch_n_acc = 0.0, 0.0

            train_batch_gen = self.pipe.batch_gen(phase='train')

            for train_batch_dict in train_batch_gen:
                train_batch_dict = self._to_tensor(train_batch_dict)

                self.optimizer.zero_grad()

                # 前向传播
                outputs = self.model(
                    word_ph=train_batch_dict['word_batch'],
                    price_ph=train_batch_dict['price_batch'],
                    stock_ph=train_batch_dict['stock_batch'],
                    T_ph=train_batch_dict['T_batch'],
                    n_words_ph=train_batch_dict['n_words_batch'],
                    n_msgs_ph=train_batch_dict['n_msgs_batch'],
                    y_ph=train_batch_dict['y_batch'],
                    ss_index_ph=train_batch_dict['ss_index_batch'],
                    is_training=True
                )

                # 计算损失
                train_batch_loss = self.model.compute_loss(outputs, train_batch_dict['T_batch'])

                # 反向传播
                train_batch_loss.backward()

                # 梯度裁剪
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.model.clip)

                # 优化步骤
                self.optimizer.step()
                self.model.step_global_step()

                # 学习率调度
                if self.scheduler is not None and self.model.global_step % self.model.decay_step == 0:
                    self.scheduler.step()

                # 统计
                train_batch_y = outputs['y_T'].detach().cpu().numpy()
                train_batch_y_ = outputs['y_T_'].detach().cpu().numpy()

                epoch_size += float(train_batch_dict['batch_size'])
                train_batch_loss_list.append(train_batch_loss.item())
                train_batch_n_acc = metrics.n_accurate_numpy(train_batch_y, train_batch_y_)
                epoch_n_acc += float(train_batch_n_acc)

                # 定期验证和保存
                if (self.model.global_step >= self.silence_step and
                        self.model.global_step % self.skip_step == 0):

                    stat_logger.print_batch_stat(
                        self.model.global_step, train_batch_loss.item(),
                        train_batch_n_acc, train_batch_dict['batch_size']
                    )

                    # 保存检查点
                    self._save_checkpoint(epoch, checkpoint_path)

                    # 验证集评估
                    res = self.generation(phase='dev')
                    stat_logger.print_eval_res(res)

                    # 切换回训练模式
                    self.model.train()

            # 打印epoch统计
            epoch_loss, epoch_acc = metrics.basic_train_stat(
                train_batch_loss_list, epoch_n_acc, epoch_size
            )
            stat_logger.print_epoch_stat(epoch_loss=epoch_loss, epoch_acc=epoch_acc)

            # 每个epoch结束保存
            self._save_checkpoint(epoch, checkpoint_path)

    def _save_checkpoint(self, epoch, checkpoint_path):
        """保存检查点"""
        os.makedirs(os.path.dirname(checkpoint_path), exist_ok=True)

        checkpoint = {
            'epoch': epoch + 1,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'global_step': self.model.global_step,
        }

        torch.save(checkpoint, checkpoint_path)
        logger.info(f'Checkpoint saved at epoch {epoch + 1}')

    def restore_and_test(self):
        """恢复模型并测试"""
        checkpoint_path = os.path.join(self.model.tf_checkpoints_path, 'model.pth')

        if os.path.exists(checkpoint_path):
            checkpoint = torch.load(checkpoint_path, map_location=self.device, weights_only=False)
            # 使用 strict=False 来兼容不同版本的模型
            missing, unexpected = self.model.load_state_dict(checkpoint['model_state_dict'], strict=False)
            if unexpected:
                logger.warning(f'Unexpected keys in checkpoint (ignored): {unexpected}')
            logger.info('Model: {0}, session restored!'.format(self.model.model_name))
        else:
            logger.info('Model: {0}: NOT found!'.format(self.model.model_name))
            raise FileNotFoundError(f"No checkpoint found at {checkpoint_path}")

        res = self.generation(phase='test', use_mcc=True)
        stat_logger.print_eval_res(res, use_mcc=True)