# Loguru 日志系统迁移文档

## 迁移概述

本项目已成功将日志系统从 Python 标准 `logging` 模块迁移到 `loguru`。

## 迁移详情

### 修改的核心文件

1. **src/video_transcript_api/utils/logger.py**
   - 完全重构以使用 loguru
   - 保留了 `setup_logger()` 函数接口以确保向后兼容
   - 新增全局配置标志防止重复配置

2. **src/video_transcript_api/utils/__init__.py**
   - 添加了 `logger` 的导出
   - 其他导出保持不变

3. **src/video_transcript_api/transcriber/capswriter_client.py**
   - 将 `import logging` 替换为 `from loguru import logger`
   - 删除了 `_setup_logger()` 方法
   - 简化了 `log()` 方法

4. **src/video_transcript_api/utils/llm.py**
   - 将 `import logging` 替换为 `from loguru import logger`
   - 所有日志调用改为使用 loguru
   - 日志消息改为英文（符合项目规范）

5. **main.py**
   - 在导入其他模块前调用 `setup_logger()` 初始化日志系统

### 日志格式变化

**旧格式**（Python logging）:
```
2025-10-19 23:20:35,330 - api_server - INFO - 从URL中解析出平台: bilibili
```

**新格式**（loguru）:

**控制台输出**:
```
2025-10-21 14:37:14 | INFO     | __main__:test_logger:25 - This is an info message
```
- 彩色输出
- 包含模块名、函数名、行号

**文件输出**:
```
2025-10-21 14:37:14 | INFO     | video_transcript_api.utils.user_manager:_load_users_config:49 - 加载用户配置成功
```
- 纯文本格式
- 完整的调用链信息

### 日志配置

日志配置在 `config/config.json` 中的 `log` 部分：

```json
{
  "log": {
    "level": "INFO",
    "file": "./data/logs/app.log",
    "max_size": 10485760,
    "backup_count": 5
  }
}
```

### 向后兼容性

- 所有使用 `setup_logger("name")` 的代码无需修改
- `setup_logger()` 现在返回 loguru 的全局 logger 实例
- 支持多次调用 `setup_logger()`，但只配置一次

### 新特性

1. **彩色控制台输出**: 不同日志级别使用不同颜色，便于快速识别
2. **更详细的上下文**: 自动包含模块名、函数名和行号
3. **异步文件写入**: 使用 `enqueue=True` 提高性能
4. **自动日志轮转**: 基于文件大小自动轮转

### 使用建议

**推荐用法**:
```python
from video_transcript_api.utils import logger

logger.info("This is an info message")
logger.warning("This is a warning")
logger.error("This is an error")
```

**兼容用法**（仍然支持）:
```python
from video_transcript_api.utils import setup_logger

logger = setup_logger("my_module")
logger.info("This is an info message")
```

### 测试

运行迁移测试脚本验证日志功能：
```bash
python tests/manual/test_loguru_migration.py
```

## 注意事项

1. loguru 已在 `requirements.txt` 中（版本 0.7.0）
2. 日志文件位于 `data/logs/app.log`
3. 所有测试脚本的控制台日志已改为英文（符合 CLAUDE.md 规范）
4. Windows 控制台可能显示中文乱码，但不影响日志文件内容

## 迁移完成日期

2025-10-21
