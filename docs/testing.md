# GYSDH Chat 测试运行指南

## 环境准备

1. 安装测试依赖：
```bash
pip install pytest pytest-django pytest-cov
```

2. 确保在项目根目录下有 `pytest.ini` 配置文件。

## 运行测试命令

### 基本测试命令

```bash
# 运行所有测试
pytest

# 显示详细输出
pytest -v

# 显示非常详细的输出（包括所有print语句）
pytest -vv
```

### 按类型运行测试

```bash
# 运行单元测试
pytest -m unit

# 运行集成测试
pytest -m integration

# 运行模型测试
pytest -m model

# 运行视图测试
pytest -m view
```

### 运行特定测试文件或类

```bash
# 运行特定测试文件
pytest gysdhChatApp/tests/test_models.py

# 运行特定测试类
pytest gysdhChatApp/tests/test_models.py::TestUserModel

# 运行特定测试方法
pytest gysdhChatApp/tests/test_models.py::TestUserModel::test_user_creation
```

### 测试覆盖率报告

```bash
# 生成基本覆盖率报告
pytest --cov=gysdhChatApp

# 生成详细的HTML覆盖率报告
pytest --cov=gysdhChatApp --cov-report=html

# 生成带行号的终端覆盖率报告
pytest --cov=gysdhChatApp --cov-report=term-missing
```

### 失败处理选项

```bash
# 在第一个测试失败时停止
pytest -x

# 在两个测试失败后停止
pytest --maxfail=2

# 显示失败测试的完整回溯
pytest --tb=long

# 仅重新运行上次失败的测试
pytest --lf

# 首先运行上次失败的测试
pytest --ff
```

### 性能分析

```bash
# 显示最慢的10个测试
pytest --durations=10

# 显示所有测试的运行时间
pytest --durations=0
```

### 并行运行测试

```bash
# 使用4个进程并行运行测试
pytest -n 4

# 自动检测CPU核心数并使用相应数量的进程
pytest -n auto
```

## 常见问题解决

1. 数据库测试失败：
```bash
# 重置测试数据库
python manage.py flush --no-input
```

2. 缓存问题：
```bash
# 清除pytest缓存
pytest --cache-clear
```

3. 测试数据库迁移：
```bash
python manage.py migrate --settings=gysdhChatProject.settings_test
```

## 最佳实践

1. 定期运行完整测试套件：
```bash
# 运行所有测试并生成覆盖率报告
pytest --cov=gysdhChatApp --cov-report=html
```

2. 在提交代码前运行测试：
```bash
# 运行快速测试检查
pytest -q
```

3. 持续集成环境中的测试：
```bash
# 生成JUnit XML报告（用于CI工具）
pytest --junitxml=test-results.xml
```

## 注意事项

- 运行测试前确保已激活虚拟环境
- 确保测试数据库配置正确
- 定期检查并更新测试用例
- 保持测试代码的整洁和可维护性
- 为新功能编写相应的测试用例
