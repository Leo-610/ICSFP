# GitHub更新指南

## 从GitHub拉取最新代码的步骤

### 方法1: 使用自动化脚本

```bash
# 运行自动化更新脚本
python update_from_github.py
```

### 方法2: 手动更新步骤

#### 1. 备份当前重要文件
```bash
# 创建备份目录
mkdir backup_$(date +%Y%m%d_%H%M%S)

# 备份重要文件
cp config_cmin-cn.yml backup_*/
cp config_cmin-us.yml backup_*/
cp granger_causality.py backup_*/
cp force_retrain_cmin.py backup_*/
cp check_cmin_data.py backup_*/

# 备份数据目录
cp -r data/ backup_*/
cp -r checkpoints/ backup_*/
cp -r log/ backup_*/
```

#### 2. 克隆最新代码
```bash
# 克隆到临时目录
git clone https://github.com/wenrui-jiang/HCSF.git HCSF_fresh

# 或者如果已有仓库，拉取最新代码
cd HCSF_fresh
git pull origin main
```

#### 3. 比较文件版本
```bash
# 比较重要文件的时间戳
ls -la Main.py HCSF_fresh/Main.py
ls -la Model.py HCSF_fresh/Model.py
ls -la Executor.py HCSF_fresh/Executor.py
ls -la DataPipe.py HCSF_fresh/DataPipe.py
ls -la ConfigLoader.py HCSF_fresh/ConfigLoader.py
```

#### 4. 更新较新的文件
```bash
# 如果GitHub版本更新，则复制过来
cp HCSF_fresh/Main.py ./
cp HCSF_fresh/Model.py ./
cp HCSF_fresh/Executor.py ./
cp HCSF_fresh/DataPipe.py ./
cp HCSF_fresh/ConfigLoader.py ./
cp HCSF_fresh/requirements.txt ./
```

#### 5. 合并配置文件
```bash
# 比较配置文件差异
diff config.yml HCSF_fresh/config.yml

# 手动合并或使用工具
# 保留你的数据路径和股票配置，但采用新的模型参数
```

#### 6. 保留自定义文件
```bash
# 确保这些文件不被覆盖
# - config_cmin-cn.yml (你的CMIN-CN配置)
# - config_cmin-us.yml (你的CMIN-US配置)  
# - granger_causality.py (Granger因果分析)
# - force_retrain_cmin.py (强制重训练脚本)
# - check_cmin_data.py (数据检查脚本)
```

#### 7. 清理临时文件
```bash
rm -rf HCSF_fresh
```

### 方法3: 使用Git命令（如果当前目录是Git仓库）

```bash
# 添加远程仓库（如果还没有）
git remote add upstream https://github.com/wenrui-jiang/HCSF.git

# 获取最新代码
git fetch upstream

# 查看差异
git diff HEAD upstream/main

# 合并最新代码（谨慎操作）
git merge upstream/main

# 或者创建新分支
git checkout -b update_from_upstream
git merge upstream/main
```

## 版本冲突处理策略

### 1. 配置文件冲突
- **保留**: 数据路径配置 (`paths`)
- **保留**: 股票列表配置 (`stocks`) 
- **更新**: 模型参数配置 (`model`)
- **更新**: 训练参数配置 (`dates`, `batch_size`等)

### 2. 代码文件冲突
- **更新**: 核心模型文件 (`Model.py`, `Executor.py`)
- **更新**: 数据处理文件 (`DataPipe.py`, `ConfigLoader.py`)
- **保留**: 自定义分析脚本

### 3. 数据文件冲突
- **保留**: 所有数据文件 (`data/`目录)
- **保留**: 训练好的模型 (`checkpoints/`目录)
- **保留**: 日志文件 (`log/`目录)

## 更新后验证步骤

### 1. 检查配置文件
```bash
python check_cmin_data.py
```

### 2. 验证数据完整性
```bash
python -c "
import yaml
with open('config_cmin-cn.yml', 'r') as f:
    config = yaml.safe_load(f)
print('股票数量:', len(config['stocks']['cmin']))
print('数据路径:', config['paths']['price'])
"
```

### 3. 测试模型加载
```bash
python -c "
from ConfigLoader import stock_symbols, path_parser
print('股票数量:', len(stock_symbols))
print('数据路径:', path_parser.movement)
"
```

### 4. 重新训练
```bash
python force_retrain_cmin.py
```

## 常见问题解决

### Q: 配置文件格式不兼容
A: 手动合并配置，保留数据相关设置，更新模型参数

### Q: 模型结构变化
A: 清除旧checkpoints，重新训练模型

### Q: 数据路径错误
A: 检查并修正配置文件中的路径设置

### Q: 依赖包版本冲突
A: 更新requirements.txt，重新安装依赖

## 推荐更新流程

1. **备份当前工作** → 运行备份脚本
2. **拉取最新代码** → 使用git或下载zip
3. **比较文件版本** → 确定哪些文件需要更新
4. **选择性更新** → 只更新核心代码，保留配置和数据
5. **验证功能** → 运行测试脚本确保一切正常
6. **重新训练** → 使用新代码训练模型

这样可以确保你获得最新的功能改进，同时保留你的数据配置和自定义分析工具。



