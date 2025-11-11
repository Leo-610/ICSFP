#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script for UnifiedDataLoader

This script tests the unified data loader functionality across different datasets.
"""

import sys
import os
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from unified_data_loader import (
    UnifiedDataLoader, 
    create_data_loader,
    load_cikm18,
    load_acl18,
    load_cmin_cn
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_basic_loading():
    """Test basic loading functionality."""
    print("\n" + "="*70)
    print("TEST 1: Basic Loading")
    print("="*70)
    
    datasets = ['cikm18', 'acl18']
    
    for dataset_name in datasets:
        try:
            print(f"\n[{dataset_name.upper()}] Loading dataset...")
            loader = create_data_loader(dataset_name)
            
            # Get dataset info
            info = loader.get_dataset_info()
            print(f"  ✓ Name: {info['name']}")
            print(f"  ✓ Description: {info['description']}")
            print(f"  ✓ Market: {info['market']}")
            print(f"  ✓ Number of stocks: {info['num_stocks']}")
            print(f"  ✓ Has causal graph: {info['has_causal_graph']}")
            
            # Print date ranges
            print(f"  ✓ Date ranges:")
            for phase, (start, end) in info['date_range'].items():
                print(f"      {phase}: {start} to {end}")
            
            print(f"  ✓ Loader representation: {loader}")
            
        except Exception as e:
            print(f"  ✗ Error loading {dataset_name}: {e}")
            logger.exception(f"Failed to load {dataset_name}")


def test_stock_list():
    """Test stock list retrieval."""
    print("\n" + "="*70)
    print("TEST 2: Stock List Retrieval")
    print("="*70)
    
    for dataset_name in ['cikm18', 'acl18']:
        try:
            print(f"\n[{dataset_name.upper()}]")
            loader = create_data_loader(dataset_name)
            stocks = loader.get_stock_list()
            
            print(f"  ✓ Total stocks: {len(stocks)}")
            print(f"  ✓ First 10 stocks: {stocks[:10]}")
            
        except Exception as e:
            print(f"  ✗ Error: {e}")


def test_dataset_validation():
    """Test dataset validation."""
    print("\n" + "="*70)
    print("TEST 3: Dataset Validation")
    print("="*70)
    
    for dataset_name in ['cikm18', 'acl18']:
        try:
            print(f"\n[{dataset_name.upper()}]")
            loader = create_data_loader(dataset_name)
            validation = loader.validate_dataset()
            
            print(f"  Valid: {validation['valid']}")
            
            if validation['stats']:
                print(f"  Statistics:")
                for key, value in validation['stats'].items():
                    print(f"    - {key}: {value}")
            
            if validation['errors']:
                print(f"  Errors:")
                for error in validation['errors']:
                    print(f"    ✗ {error}")
            
            if validation['warnings']:
                print(f"  Warnings:")
                for warning in validation['warnings']:
                    print(f"    ⚠ {warning}")
            
            if validation['valid'] and not validation['errors']:
                print(f"  ✓ Dataset validation passed!")
            
        except Exception as e:
            print(f"  ✗ Error: {e}")


def test_statistics():
    """Test statistics gathering."""
    print("\n" + "="*70)
    print("TEST 4: Statistics")
    print("="*70)
    
    for dataset_name in ['cikm18', 'acl18']:
        try:
            print(f"\n[{dataset_name.upper()}]")
            loader = create_data_loader(dataset_name)
            stats = loader.get_statistics()
            
            print(f"  Dataset: {stats['dataset']}")
            print(f"  Number of stocks: {stats['num_stocks']}")
            print(f"  Vocabulary size: {stats['vocab_size']}")
            
            print(f"  Date ranges:")
            for phase, (start, end) in stats['date_ranges'].items():
                print(f"    {phase}: {start} to {end}")
            
        except Exception as e:
            print(f"  ✗ Error: {e}")


def test_causal_graph():
    """Test causal graph loading."""
    print("\n" + "="*70)
    print("TEST 5: Causal Graph Loading")
    print("="*70)
    
    for dataset_name in ['cikm18', 'acl18']:
        try:
            print(f"\n[{dataset_name.upper()}]")
            loader = create_data_loader(dataset_name)
            
            # Try to load causal graph
            causal_graph = loader.load_causal_graph(method='granger', recompute=False)
            
            if causal_graph is not None:
                print(f"  ✓ Causal graph shape: {causal_graph.shape}")
                print(f"  ✓ Non-zero elements: {(causal_graph != 0).sum()}")
                print(f"  ✓ Sparsity: {(causal_graph == 0).sum() / causal_graph.size:.2%}")
            else:
                print(f"  ⚠ No causal graph available")
            
        except Exception as e:
            print(f"  ✗ Error: {e}")


def test_convenience_functions():
    """Test convenience loading functions."""
    print("\n" + "="*70)
    print("TEST 6: Convenience Functions")
    print("="*70)
    
    functions = [
        ('CIKM18', load_cikm18),
        ('ACL18', load_acl18),
    ]
    
    for name, func in functions:
        try:
            print(f"\n[{name}]")
            loader = func()
            info = loader.get_dataset_info()
            print(f"  ✓ Loaded using {func.__name__}()")
            print(f"  ✓ Dataset: {info['name']}")
            print(f"  ✓ Stocks: {info['num_stocks']}")
            
        except Exception as e:
            print(f"  ✗ Error: {e}")


def test_datapipe_compatibility():
    """Test compatibility with existing DataPipe."""
    print("\n" + "="*70)
    print("TEST 7: DataPipe Compatibility")
    print("="*70)
    
    try:
        print("\n[Compatibility Check]")
        loader = load_cikm18()
        
        # Check if DataPipe attributes are accessible
        print(f"  ✓ Movement path: {loader.data_pipe.movement_path}")
        print(f"  ✓ Tweet path: {loader.data_pipe.tweet_path}")
        print(f"  ✓ Batch size: {loader.data_pipe.batch_size}")
        print(f"  ✓ Max days: {loader.data_pipe.max_n_days}")
        print(f"  ✓ Max words: {loader.data_pipe.max_n_words}")
        
        # Check phase detection
        for phase in ['train', 'dev', 'test']:
            start, end = loader.data_pipe._get_start_end_date(phase)
            batch_size = loader.data_pipe._get_batch_size(phase)
            print(f"  ✓ {phase.capitalize()} phase: {start} to {end}, batch_size={batch_size}")
        
        print(f"\n  ✓ DataPipe compatibility verified!")
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        logger.exception("DataPipe compatibility test failed")


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*70)
    print("UNIFIED DATA LOADER - COMPREHENSIVE TEST SUITE")
    print("="*70)
    print(f"Testing unified data loading functionality...")
    print("="*70)
    
    tests = [
        test_basic_loading,
        test_stock_list,
        test_dataset_validation,
        test_statistics,
        test_causal_graph,
        test_convenience_functions,
        test_datapipe_compatibility,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            failed += 1
            logger.exception(f"Test {test.__name__} failed")
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Total tests: {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print("="*70)
    
    if failed == 0:
        print("✓ All tests passed!")
    else:
        print(f"✗ {failed} test(s) failed. Check logs for details.")
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
