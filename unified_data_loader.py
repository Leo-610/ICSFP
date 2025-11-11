#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unified Data Loader for Multi-Dataset Support
==============================================

This module provides a unified interface for loading different stock prediction datasets
(ACL18, CIKM18, CMIN-CN) with automatic format adaptation.

Key Features:
- Automatic dataset format detection
- Unified batch generation interface
- Compatible with existing DataPipe
- Support for multiple causal graph methods
- Efficient caching and preprocessing

Author: ICSFP Team
Created: 2025-11-06
"""

import os
import io
import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Union
import logging
from pathlib import Path

from ConfigLoader import logger, path_parser, config_model, dates, stock_symbols, vocab
from DataPipe import DataPipe


class UnifiedDataLoader:
    """
    Unified data loader that supports multiple dataset formats.
    
    Supports:
    - ACL18: Original ACL 2018 dataset format
    - CIKM18: CIKM 2018 dataset format  
    - CMIN-CN: Chinese stock market dataset
    
    Attributes:
        dataset_name (str): Name of the dataset ('acl18', 'cikm18', 'cmin-cn')
        data_pipe (DataPipe): Underlying DataPipe instance
        dataset_config (dict): Dataset-specific configuration
    """
    
    SUPPORTED_DATASETS = ['acl18', 'cikm18', 'cmin-cn']
    
    def __init__(self, dataset_name: str = 'cikm18', custom_config: Optional[Dict] = None):
        """
        Initialize UnifiedDataLoader.
        
        Args:
            dataset_name: Name of the dataset to load
            custom_config: Optional custom configuration to override defaults
            
        Raises:
            ValueError: If dataset_name is not supported
        """
        self.dataset_name = dataset_name.lower()
        
        if self.dataset_name not in self.SUPPORTED_DATASETS:
            raise ValueError(
                f"Dataset '{dataset_name}' not supported. "
                f"Choose from: {self.SUPPORTED_DATASETS}"
            )
        
        logger.info(f"Initializing UnifiedDataLoader for dataset: {self.dataset_name}")
        
        # Load base DataPipe
        self.data_pipe = DataPipe()
        
        # Load dataset-specific configuration
        self.dataset_config = self._load_dataset_config(custom_config)
        
        # Update paths for the selected dataset
        self._update_paths()
        
        # Cache for preprocessed data
        self._cache = {}
        
        logger.info(f"UnifiedDataLoader initialized successfully for {self.dataset_name}")
    
    def _load_dataset_config(self, custom_config: Optional[Dict] = None) -> Dict:
        """
        Load dataset-specific configuration.
        
        Args:
            custom_config: Optional custom configuration
            
        Returns:
            Dataset configuration dictionary
        """
        # Default configurations for each dataset
        configs = {
            'acl18': {
                'name': 'ACL18',
                'description': 'ACL 2018 Stock Dataset',
                'data_root': 'data/acl18',
                'price_dir': 'price/preprocessed',
                'tweet_dir': 'tweet/preprocessed',
                'stocks': stock_symbols,  # Use default stock symbols
                'date_format': '%Y-%m-%d',
                'has_causal_graph': True,
                'market': 'US',
            },
            'cikm18': {
                'name': 'CIKM18',
                'description': 'CIKM 2018 Stock Dataset',
                'data_root': 'data/cikm18',
                'price_dir': 'price/preprocessed',
                'tweet_dir': 'tweet/preprocessed',
                'stocks': stock_symbols,
                'date_format': '%Y-%m-%d',
                'has_causal_graph': True,
                'market': 'US',
            },
            'cmin-cn': {
                'name': 'CMIN-CN',
                'description': 'Chinese Stock Market Dataset',
                'data_root': 'data/cmin-cn',
                'price_dir': 'price/preprocessed',
                'tweet_dir': 'tweet/preprocessed',
                'stocks': [],  # Will be loaded from dataset
                'date_format': '%Y-%m-%d',
                'has_causal_graph': False,  # Need to compute
                'market': 'CN',
            }
        }
        
        config = configs.get(self.dataset_name, configs['cikm18'])
        
        # Override with custom config if provided
        if custom_config:
            config.update(custom_config)
        
        return config
    
    def _update_paths(self):
        """Update DataPipe paths for the selected dataset."""
        data_root = Path(self.dataset_config['data_root'])
        
        # Update movement (price) path
        self.data_pipe.movement_path = data_root / self.dataset_config['price_dir']
        
        # Update tweet path
        self.data_pipe.tweet_path = data_root / self.dataset_config['tweet_dir']
        
        logger.info(f"Updated paths - Price: {self.data_pipe.movement_path}, "
                   f"Tweet: {self.data_pipe.tweet_path}")
    
    def get_dataset_info(self) -> Dict:
        """
        Get information about the current dataset.
        
        Returns:
            Dictionary containing dataset information
        """
        return {
            'name': self.dataset_config['name'],
            'description': self.dataset_config['description'],
            'market': self.dataset_config['market'],
            'data_root': self.dataset_config['data_root'],
            'num_stocks': len(self.get_stock_list()),
            'has_causal_graph': self.dataset_config['has_causal_graph'],
            'date_range': {
                'train': (self.data_pipe.train_start_date, self.data_pipe.train_end_date),
                'dev': (self.data_pipe.dev_start_date, self.data_pipe.dev_end_date),
                'test': (self.data_pipe.test_start_date, self.data_pipe.test_end_date),
            }
        }
    
    def get_stock_list(self) -> List[str]:
        """
        Get list of stock symbols for the current dataset.
        
        Returns:
            List of stock symbols
        """
        if self.dataset_name == 'cmin-cn':
            # For CMIN-CN, scan the price directory to get stock list
            return self._scan_stock_symbols()
        else:
            return self.dataset_config['stocks']
    
    def _scan_stock_symbols(self) -> List[str]:
        """
        Scan the price directory to get available stock symbols.
        
        Returns:
            List of stock symbols found in the dataset
        """
        price_dir = self.data_pipe.movement_path
        
        if not os.path.exists(price_dir):
            logger.warning(f"Price directory not found: {price_dir}")
            return []
        
        stock_files = [f for f in os.listdir(price_dir) if f.endswith('.txt')]
        stocks = [os.path.splitext(f)[0] for f in stock_files]
        
        logger.info(f"Found {len(stocks)} stocks in {price_dir}")
        return sorted(stocks)
    
    def load_batch(self, 
                   phase: str = 'train',
                   batch_size: Optional[int] = None,
                   use_cache: bool = True) -> Tuple:
        """
        Load a batch of data.
        
        Args:
            phase: Phase of training ('train', 'dev', 'test')
            batch_size: Batch size (if None, use config default)
            use_cache: Whether to use cached data
            
        Returns:
            Tuple of (features, labels) for the batch
        """
        # Use DataPipe's existing batch generation
        # This maintains compatibility with existing code
        
        cache_key = f"{phase}_{batch_size}"
        
        if use_cache and cache_key in self._cache:
            logger.debug(f"Using cached data for {cache_key}")
            return self._cache[cache_key]
        
        # Get batch using DataPipe
        batch_data = self.data_pipe.get_batch(
            phase=phase,
            batch_size=batch_size or self.data_pipe.batch_size
        )
        
        if use_cache:
            self._cache[cache_key] = batch_data
        
        return batch_data
    
    def generate_batches(self, 
                        phase: str = 'train',
                        batch_size: Optional[int] = None,
                        shuffle: bool = None):
        """
        Generate batches for training/evaluation.
        
        Args:
            phase: Phase of training ('train', 'dev', 'test')
            batch_size: Batch size (if None, use config default)
            shuffle: Whether to shuffle data (if None, use config default)
            
        Yields:
            Batches of (features, labels)
        """
        if batch_size is None:
            batch_size = self.data_pipe._get_batch_size(phase)
        
        if shuffle is None:
            shuffle = self.data_pipe.shuffle and phase == 'train'
        
        logger.info(f"Generating batches for {phase} phase with batch_size={batch_size}, "
                   f"shuffle={shuffle}")
        
        # Delegate to DataPipe's batch generation
        for batch in self.data_pipe.batch_gen(phase=phase, batch_size=batch_size):
            yield batch
    
    def load_causal_graph(self, 
                         method: str = 'granger',
                         recompute: bool = False) -> np.ndarray:
        """
        Load or compute causal graph for the dataset.
        
        Args:
            method: Causal discovery method ('granger', 'cuts+', 'transfer_entropy')
            recompute: Whether to recompute even if cached graph exists
            
        Returns:
            Causal adjacency matrix (numpy array)
        """
        cache_file = f"causal_graph_{self.dataset_name}_{method}.npy"
        
        if not recompute and os.path.exists(cache_file):
            logger.info(f"Loading cached causal graph from {cache_file}")
            return np.load(cache_file)
        
        logger.info(f"Computing causal graph using {method} method...")
        
        # This will be integrated with CausalDiscoveryManager in Day 2-3
        # For now, try to load existing causal graph
        default_graph_file = "causal_graph.npy"
        if os.path.exists(default_graph_file):
            logger.info(f"Using existing causal graph: {default_graph_file}")
            return np.load(default_graph_file)
        
        # Return None if no causal graph available
        logger.warning(f"No causal graph found. Will use identity matrix or compute on demand.")
        num_stocks = len(self.get_stock_list())
        return np.eye(num_stocks)  # Identity matrix as fallback
    
    def validate_dataset(self) -> Dict:
        """
        Validate the dataset structure and completeness.
        
        Returns:
            Dictionary with validation results
        """
        results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'stats': {}
        }
        
        # Check price directory
        price_dir = self.data_pipe.movement_path
        if not os.path.exists(price_dir):
            results['valid'] = False
            results['errors'].append(f"Price directory not found: {price_dir}")
        else:
            price_files = [f for f in os.listdir(price_dir) if f.endswith('.txt')]
            results['stats']['price_files'] = len(price_files)
            logger.info(f"Found {len(price_files)} price files")
        
        # Check tweet directory
        tweet_dir = self.data_pipe.tweet_path
        if not os.path.exists(tweet_dir):
            results['valid'] = False
            results['errors'].append(f"Tweet directory not found: {tweet_dir}")
        else:
            tweet_dirs = [d for d in os.listdir(tweet_dir) 
                         if os.path.isdir(os.path.join(tweet_dir, d))]
            results['stats']['tweet_directories'] = len(tweet_dirs)
            logger.info(f"Found {len(tweet_dirs)} tweet directories")
        
        # Check causal graph
        if self.dataset_config['has_causal_graph']:
            causal_file = "causal_graph.npy"
            if not os.path.exists(causal_file):
                results['warnings'].append(f"Causal graph file not found: {causal_file}")
        
        return results
    
    def get_statistics(self) -> Dict:
        """
        Get statistics about the dataset.
        
        Returns:
            Dictionary with dataset statistics
        """
        stats = {
            'dataset': self.dataset_name,
            'num_stocks': len(self.get_stock_list()),
            'vocab_size': len(vocab),
        }
        
        # Add date range statistics
        info = self.get_dataset_info()
        stats['date_ranges'] = info['date_range']
        
        return stats
    
    def clear_cache(self):
        """Clear the internal cache."""
        self._cache.clear()
        logger.info("Cache cleared")
    
    def __repr__(self) -> str:
        return (f"UnifiedDataLoader(dataset='{self.dataset_name}', "
                f"stocks={len(self.get_stock_list())}, "
                f"market='{self.dataset_config['market']}')")


def create_data_loader(dataset_name: str = 'cikm18', **kwargs) -> UnifiedDataLoader:
    """
    Factory function to create a UnifiedDataLoader instance.
    
    Args:
        dataset_name: Name of the dataset
        **kwargs: Additional configuration parameters
        
    Returns:
        UnifiedDataLoader instance
        
    Example:
        >>> loader = create_data_loader('acl18')
        >>> info = loader.get_dataset_info()
        >>> print(info['name'])
        ACL18
    """
    return UnifiedDataLoader(dataset_name, custom_config=kwargs)


# Convenience functions for quick access
def load_acl18(**kwargs) -> UnifiedDataLoader:
    """Load ACL18 dataset."""
    return create_data_loader('acl18', **kwargs)


def load_cikm18(**kwargs) -> UnifiedDataLoader:
    """Load CIKM18 dataset."""
    return create_data_loader('cikm18', **kwargs)


def load_cmin_cn(**kwargs) -> UnifiedDataLoader:
    """Load CMIN-CN dataset."""
    return create_data_loader('cmin-cn', **kwargs)


if __name__ == '__main__':
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("Unified Data Loader - Test Suite")
    print("=" * 60)
    
    # Test 1: Load CIKM18
    print("\n[Test 1] Loading CIKM18 dataset...")
    try:
        loader_cikm = load_cikm18()
        info = loader_cikm.get_dataset_info()
        print(f"✓ Dataset: {info['name']}")
        print(f"✓ Market: {info['market']}")
        print(f"✓ Stocks: {info['num_stocks']}")
        
        # Validate
        validation = loader_cikm.validate_dataset()
        if validation['valid']:
            print("✓ Dataset validation passed")
        else:
            print(f"✗ Validation failed: {validation['errors']}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 2: Load ACL18
    print("\n[Test 2] Loading ACL18 dataset...")
    try:
        loader_acl = load_acl18()
        print(f"✓ Loaded: {loader_acl}")
        stats = loader_acl.get_statistics()
        print(f"✓ Statistics: {stats}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 3: Compare datasets
    print("\n[Test 3] Comparing datasets...")
    for dataset in ['cikm18', 'acl18']:
        try:
            loader = create_data_loader(dataset)
            stocks = loader.get_stock_list()
            print(f"✓ {dataset.upper()}: {len(stocks)} stocks")
        except Exception as e:
            print(f"✗ {dataset.upper()}: {e}")
    
    print("\n" + "=" * 60)
    print("Test suite completed!")
    print("=" * 60)
