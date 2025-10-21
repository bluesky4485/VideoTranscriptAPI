# Logger 使用指南

## 快速开始

### 基本用法

```python
# 方式 1: 直接使用全局 logger（推荐）
from video_transcript_api.utils import logger

logger.info("This is an info message")
logger.warning("This is a warning")
logger.error("This is an error")
logger.debug("This is a debug message")

# 方式 2: 使用 setup_logger（兼容旧代码）
from video_transcript_api.utils import setup_logger

log = setup_logger("module_name")
log.info("This is an info message")
```

### 日志级别

loguru 支持以下日志级别（从低到高）：

- `logger.trace()` - 最详细的调试信息
- `logger.debug()` - 调试信息
- `logger.info()` - 一般信息
- `logger.success()` - 成功信息（loguru 特有）
- `logger.warning()` - 警告信息
- `logger.error()` - 错误信息
- `logger.critical()` - 严重错误

### 异常日志

```python
try:
    risky_operation()
except Exception as e:
    # 自动记录完整的异常堆栈
    logger.exception("Operation failed")
    # 或者
    logger.error(f"Operation failed: {e}")
```

### 带上下文的日志

```python
# 使用 f-string 格式化
user_id = 12345
logger.info(f"User {user_id} logged in")

# loguru 会自动包含调用位置信息
# 输出: 2025-10-21 14:37:14 | INFO | module:function:42 - User 12345 logged in
```

## 配置

日志配置在 `config/config.json`:

```json
{
  "log": {
    "level": "INFO",           // 日志级别: DEBUG, INFO, WARNING, ERROR
    "file": "./data/logs/app.log",  // 日志文件路径
    "max_size": 10485760,      // 单个文件最大大小（字节）
    "backup_count": 5          // 保留的备份文件数量
  }
}
```

## 输出格式

### 控制台输出（彩色）
```
2025-10-21 14:37:14 | INFO     | module:function:line - message
```

### 文件输出（纯文本）
```
2025-10-21 14:37:14 | INFO     | video_transcript_api.utils.module:function:line - message
```

## 最佳实践

### ✅ 推荐

```python
# 1. 使用描述性的日志消息
logger.info("User authentication successful", user_id=user_id)

# 2. 在关键操作前后记录日志
logger.info("Starting video download...")
download_video(url)
logger.info("Video download completed")

# 3. 记录异常时使用 exception()
try:
    process_data()
except Exception:
    logger.exception("Failed to process data")
```

### ❌ 避免

```python
# 1. 避免在循环中过度记录
for item in large_list:
    logger.debug(f"Processing {item}")  # 太多日志

# 2. 避免记录敏感信息
logger.info(f"User password: {password}")  # 危险！

# 3. 避免使用 print() 代替日志
print("This is bad")  # 应该使用 logger.info()
```

## 性能考虑

1. **日志级别**: 生产环境使用 INFO 或 WARNING
2. **异步写入**: loguru 已配置异步文件写入 (`enqueue=True`)
3. **条件日志**: 只在必要时记录详细信息

```python
if logger.level("DEBUG").no >= logger._core.min_level:
    expensive_debug_info = compute_debug_info()
    logger.debug(f"Debug info: {expensive_debug_info}")
```

## 调试技巧

### 临时启用调试日志

```python
from loguru import logger

# 临时添加调试级别的控制台输出
debug_id = logger.add(
    sys.stdout,
    level="DEBUG",
    format="{time} | {level} | {message}"
)

# 调试完成后移除
logger.remove(debug_id)
```

### 查看最近的日志

```bash
# Linux/Mac
tail -f data/logs/app.log

# Windows
Get-Content data/logs/app.log -Tail 50 -Wait
```

## 常见问题

### Q: 如何改变日志级别？
A: 修改 `config/config.json` 中的 `log.level` 配置。

### Q: 日志文件在哪里？
A: 默认在 `data/logs/app.log`。

### Q: 如何禁用彩色输出？
A: 修改 `src/video_transcript_api/utils/logger.py` 中的 `colorize=True` 为 `False`。

### Q: 旧代码需要修改吗？
A: 不需要。`setup_logger()` 已经兼容，返回 loguru logger。

## 参考资料

- [Loguru 官方文档](https://loguru.readthedocs.io/)
- [项目迁移文档](./LOGURU_MIGRATION.md)
