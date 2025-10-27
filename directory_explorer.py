#!/usr/bin/env python3
"""
HCSF项目目录结构探索脚本
遍历并显示项目的目录结构（两级深度）
"""

import os
from pathlib import Path


def explore_directory_structure(root_path=".", max_depth=2):
    """
    探索目录结构

    Args:
        root_path: 根目录路径
        max_depth: 最大深度（2表示显示两级目录）
    """
    root = Path(root_path)

    print(f"HCSF项目目录结构 (根目录: {root.absolute()})")
    print("=" * 60)

    def show_tree(path, prefix="", depth=0):
        if depth > max_depth:
            return

        items = []
        try:
            # 获取所有项目（文件夹和文件）
            for item in sorted(path.iterdir()):
                if not item.name.startswith('.'):  # 跳过隐藏文件/文件夹
                    items.append(item)
        except PermissionError:
            print(f"{prefix}[权限拒绝]")
            return

        for i, item in enumerate(items):
            is_last = i == len(items) - 1

            if item.is_dir():
                # 目录
                current_prefix = "└── " if is_last else "├── "
                print(f"{prefix}{current_prefix}{item.name}/")

                # 递归显示子目录
                if depth < max_depth:
                    next_prefix = prefix + ("    " if is_last else "│   ")
                    show_tree(item, next_prefix, depth + 1)
            else:
                # 文件
                current_prefix = "└── " if is_last else "├── "

                # 显示文件大小
                try:
                    size = item.stat().st_size
                    size_str = format_file_size(size)
                    print(f"{prefix}{current_prefix}{item.name} ({size_str})")
                except:
                    print(f"{prefix}{current_prefix}{item.name}")

    # 显示根目录
    print(f"{root.name}/")
    show_tree(root, "", 0)

    # 统计信息
    print("\n" + "=" * 60)
    print("目录统计信息:")

    total_dirs = 0
    total_files = 0
    key_files = {
        'Python文件': [],
        'YAML配置文件': [],
        '数据文件': [],
        'CUTS+相关': [],
        'StockNet相关': []
    }

    def count_items(path, depth=0):
        nonlocal total_dirs, total_files

        if depth > max_depth:
            return

        try:
            for item in path.iterdir():
                if item.name.startswith('.'):
                    continue

                if item.is_dir():
                    total_dirs += 1
                    # 特殊目录识别
                    if 'data' in item.name.lower():
                        key_files['数据文件'].append(str(item.relative_to(root)))

                    # 递归计数
                    if depth < max_depth:
                        count_items(item, depth + 1)
                else:
                    total_files += 1
                    rel_path = str(item.relative_to(root))

                    # 文件类型分类
                    if item.suffix == '.py':
                        key_files['Python文件'].append(rel_path)

                        # 检查是否是关键文件
                        if 'cuts' in item.name.lower():
                            key_files['CUTS+相关'].append(rel_path)
                        elif any(keyword in item.name.lower() for keyword in ['stock', 'model', 'main']):
                            key_files['StockNet相关'].append(rel_path)

                    elif item.suffix in ['.yaml', '.yml']:
                        key_files['YAML配置文件'].append(rel_path)
                    elif item.suffix in ['.txt', '.csv', '.json']:
                        key_files['数据文件'].append(rel_path)
        except PermissionError:
            pass

    count_items(root, 0)

    print(f"总目录数: {total_dirs}")
    print(f"总文件数: {total_files}")

    print("\n关键文件分类:")
    for category, files in key_files.items():
        if files:
            print(f"\n{category}:")
            for file in files[:10]:  # 只显示前10个
                print(f"  - {file}")
            if len(files) > 10:
                print(f"  ... 还有 {len(files) - 10} 个文件")


def format_file_size(size_bytes):
    """格式化文件大小"""
    if size_bytes == 0:
        return "0B"

    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1

    return f"{size_bytes:.1f}{size_names[i]}"


def find_key_files():
    """查找关键文件"""
    print("\n" + "=" * 60)
    print("关键文件查找:")

    key_patterns = {
        'CUTS+核心文件': ['cuts_plus.py', 'cuts_plus_net.py'],
        'StockNet核心文件': ['Model.py', 'Main.py', 'DataPipe.py', 'Executor.py'],
        '配置文件': ['config.yml', '*.yaml'],
        '数据目录': ['data/', 'dataset/'],
        '工具文件': ['utils/', 'tools/']
    }

    root = Path('.')

    for category, patterns in key_patterns.items():
        print(f"\n{category}:")
        found = False

        for pattern in patterns:
            if pattern.endswith('/'):
                # 查找目录
                for item in root.rglob(pattern[:-1]):
                    if item.is_dir():
                        print(f"  ✓ {item}")
                        found = True
            elif '*' in pattern:
                # 通配符模式
                for item in root.rglob(pattern):
                    print(f"  ✓ {item}")
                    found = True
            else:
                # 查找具体文件
                for item in root.rglob(pattern):
                    print(f"  ✓ {item}")
                    found = True

        if not found:
            print(f"  ✗ 未找到相关文件")


def check_data_structure():
    """检查数据结构"""
    print("\n" + "=" * 60)
    print("数据结构检查:")

    data_root = Path('./data')
    if not data_root.exists():
        print("✗ data目录不存在")
        return

    print("✓ data目录存在")

    # 检查StockNet数据结构
    expected_dirs = ['price', 'tweet']
    for dir_name in expected_dirs:
        dir_path = data_root / dir_name
        if dir_path.exists():
            print(f"✓ {dir_name}/ 目录存在")

            # 检查子目录
            subdirs = [d for d in dir_path.iterdir() if d.is_dir()]
            files = [f for f in dir_path.iterdir() if f.is_file()]

            print(f"  - 子目录数: {len(subdirs)}")
            print(f"  - 文件数: {len(files)}")

            if subdirs:
                print(f"  - 子目录: {[d.name for d in subdirs[:5]]}")
            if files:
                print(f"  - 文件示例: {[f.name for f in files[:3]]}")
        else:
            print(f"✗ {dir_name}/ 目录不存在")


if __name__ == "__main__":
    print("HCSF项目结构分析工具")
    print("正在分析项目结构...")

    # 探索目录结构
    explore_directory_structure(".", max_depth=2)

    # 查找关键文件
    find_key_files()

    # 检查数据结构
    check_data_structure()

    print("\n" + "=" * 60)
    print("分析完成！请将上述输出发送给我，我将基于此信息为你创建适配代码。")