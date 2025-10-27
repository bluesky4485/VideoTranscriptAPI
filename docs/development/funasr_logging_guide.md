# FunASR 兼容格式日志指南

## 日志级别说明

FunASR 格式生成过程使用了分层的日志系统，不同级别的日志提供不同详细程度的信息。

### 日志级别层次

```
ERROR   - 致命错误，导致无法继续
WARNING - 警告信息，不影响主流程但需要注意
INFO    - 重要的流程信息
DEBUG   - 详细的调试信息
```

---

## 正常流程日志

### 成功场景

```
[INFO] 开始生成 FunASR 兼容格式 JSON...
[INFO] 输入数据: text=243 字符, tokens=205, timestamps=205
[DEBUG] 开始创建 segments: text=243, tokens=205, timestamps=205
[DEBUG] Token 位置映射完成: reconstructed length=217
[DEBUG] 按标点分句: 6 个句子
[DEBUG] 对齐检查通过: diff=0
[DEBUG] 句子 1: 12 字符 -> tokens[0:11] -> 0.08s-1.50s
[DEBUG] 句子 2: 60 字符 -> tokens[12:68] -> 1.70s-12.20s
[DEBUG] 句子 3: 76 字符 -> tokens[69:135] -> 12.78s-26.40s
[DEBUG] 句子 4: 20 字符 -> tokens[136:155] -> 26.64s-30.74s
[DEBUG] 句子 5: 14 字符 -> tokens[156:169] -> 30.90s-33.82s
[DEBUG] 句子 6: 35 字符 -> tokens[170:204] -> 33.94s-39.76s
[DEBUG] 初始分段完成: 6 个 segments
[DEBUG] 长度优化完成: 3 个 segments
[INFO] Segments 生成完成: 3 个片段, 2/3 在目标范围内
[INFO] 成功创建 3 个 segments
[INFO] Segments 统计: 总时长=38.86s, 平均长度=81.0字符
[INFO] ✓ 已生成 FunASR 兼容文件: transcript_capswriter.json (3 个片段)
```

**关键信息**：
- ✅ 对齐检查通过（diff=0）
- ✅ 生成了 3 个片段
- ✅ 2/3 片段在目标长度范围内（80-300）
- ✅ 文件成功保存

---

## 异常场景日志

### 场景1: 文本为空

```
[INFO] 开始生成 FunASR 兼容格式 JSON...
[WARNING] 警告: 文本为空，跳过 FunASR 格式生成
[WARNING] ✗ 生成 FunASR 兼容格式失败: text is empty
[WARNING]   提示: 主要转录文件（txt）已正常生成，可忽略此警告
```

**影响**：主流程不受影响，txt 文件正常生成

---

### 场景2: Tokens 或 Timestamps 为空

```
[INFO] 开始生成 FunASR 兼容格式 JSON...
[WARNING] 警告: tokens 或 timestamps 为空 (tokens=0, timestamps=0)
[WARNING] ✗ 生成 FunASR 兼容格式失败: tokens or timestamps is empty
[WARNING]   提示: 主要转录文件（txt）已正常生成，可忽略此警告
```

**影响**：主流程不受影响，txt 文件正常生成

---

### 场景3: 长度不匹配

```
[INFO] 开始生成 FunASR 兼容格式 JSON...
[INFO] 输入数据: text=243 字符, tokens=100, timestamps=205
[DEBUG] 开始创建 segments: text=243, tokens=100, timestamps=205
[WARNING] 长度不匹配: tokens=100, timestamps=205
[INFO] 已截断至相同长度: 100
[DEBUG] Token 位置映射完成: reconstructed length=98
[DEBUG] 按标点分句: 6 个句子
[WARNING] 对齐警告: text_clean=217, reconstructed=98, diff=119
[WARNING]   这可能导致时间戳不准确，请检查输入数据
[INFO] ✓ 已生成 FunASR 兼容文件: transcript_capswriter.json (2 个片段)
```

**影响**：
- ⚠️ 时间戳可能不准确
- ⚠️ 部分文本可能丢失
- ✅ 主流程正常完成

---

### 场景4: 未生成任何 Segments

```
[INFO] 开始生成 FunASR 兼容格式 JSON...
[INFO] 输入数据: text=243 字符, tokens=205, timestamps=205
[DEBUG] 开始创建 segments: text=243, tokens=205, timestamps=205
[DEBUG] Token 位置映射完成: reconstructed length=217
[DEBUG] 按标点分句: 6 个句子
[DEBUG] 初始分段完成: 0 个 segments
[WARNING] 未生成任何 segments
[WARNING] 警告: 未生成任何 segments，跳过 FunASR 格式生成
[WARNING] ✗ 生成 FunASR 兼容格式失败: no segments generated
[WARNING]   提示: 主要转录文件（txt）已正常生成，可忽略此警告
```

**影响**：主流程不受影响，txt 文件正常生成

---

### 场景5: 文件写入失败

```
[INFO] 开始生成 FunASR 兼容格式 JSON...
[INFO] 输入数据: text=243 字符, tokens=205, timestamps=205
[INFO] 成功创建 3 个 segments
[INFO] Segments 统计: 总时长=38.86s, 平均长度=81.0字符
[WARNING] ✗ 生成 FunASR 兼容格式失败: [Errno 13] Permission denied: 'transcript_capswriter.json'
[WARNING]   提示: 主要转录文件（txt）已正常生成，可忽略此警告
[WARNING]   详细错误: Traceback (most recent call last):
  File "capswriter_client.py", line 633, in _save_results
    with open(funasr_file, "w", encoding="utf-8") as f:
PermissionError: [Errno 13] Permission denied: 'transcript_capswriter.json'
```

**影响**：
- ❌ FunASR 文件未生成
- ✅ 主流程正常完成
- 💡 需要检查文件权限

---

## 日志级别配置

### 生产环境（推荐）

```python
from video_transcript_api.utils.logging import load_config

# config.yaml
log:
  level: "INFO"  # 只显示 INFO 及以上级别
```

**显示内容**：
- ✅ 关键流程信息
- ✅ 警告和错误
- ❌ 详细的 DEBUG 信息

### 开发/调试环境

```python
# config.yaml
log:
  level: "DEBUG"  # 显示所有日志
```

**显示内容**：
- ✅ 所有级别的日志
- ✅ 详细的执行步骤
- ✅ 每个句子的映射细节

### 静默模式

```python
# config.yaml
log:
  level: "ERROR"  # 只显示错误
```

**显示内容**：
- ❌ 不显示 INFO 和 WARNING
- ✅ 只显示致命错误
- ⚠️ 可能错过重要警告

---

## 故障排查指南

### 问题1: FunASR 文件未生成

**检查日志**：
```
[WARNING] ✗ 生成 FunASR 兼容格式失败: ...
```

**排查步骤**：
1. 查看 warning 日志中的具体错误信息
2. 检查是否有 "文本为空" 或 "tokens 为空" 警告
3. 如果是文件权限问题，检查输出目录权限
4. 如果是对齐问题，检查 CapsWriter 服务器返回的数据

---

### 问题2: 时间戳不准确

**检查日志**：
```
[WARNING] 对齐警告: text_clean=217, reconstructed=98, diff=119
[WARNING]   这可能导致时间戳不准确，请检查输入数据
```

**原因分析**：
- tokens 数量与文本长度严重不匹配
- 可能是 tokens 被截断或数据不完整

**解决方法**：
1. 检查 CapsWriter 服务器配置
2. 验证音频文件完整性
3. 重新转录音频

---

### 问题3: Segments 数量异常

**检查日志**：
```
[INFO] Segments 生成完成: 1 个片段, 0/1 在目标范围内
```

**原因分析**：
- 音频太短（< 80 字符）
- 标点符号缺失，无法正常分句

**解决方法**：
1. 调整 min_len 和 max_len 参数
2. 检查转录文本是否有标点

---

## 日志文件位置

默认日志输出位置：
```
logs/
├── app.log              # 应用主日志
└── error.log            # 错误日志
```

查看 FunASR 相关日志：
```bash
# 查看所有 FunASR 相关日志
grep "FunASR" logs/app.log

# 查看警告和错误
grep -E "WARNING|ERROR" logs/app.log | grep FunASR

# 查看最近的转录
tail -f logs/app.log | grep FunASR
```

---

## 最佳实践

### 1. 生产环境

```yaml
# config.yaml
log:
  level: "INFO"
  enable_file: true
  rotation: "100 MB"
  retention: "30 days"
```

**原因**：
- 平衡日志详细程度和文件大小
- 保留足够信息用于故障排查
- 避免磁盘空间耗尽

### 2. 开发环境

```yaml
# config.yaml
log:
  level: "DEBUG"
  enable_console: true
```

**原因**：
- 实时查看详细执行过程
- 快速定位问题
- 理解算法运行细节

### 3. 监控警告

建议设置日志监控，当出现以下关键字时发送告警：
- `✗ 生成 FunASR 兼容格式失败`
- `对齐警告`
- `长度不匹配`

---

## 总结

增强的日志系统提供了：

✅ **多层次信息**：从概要到详细的分层日志
✅ **清晰的状态标识**：✓ 成功，✗ 失败，⚠️ 警告
✅ **完整的错误追踪**：包含堆栈信息用于调试
✅ **用户友好提示**：明确说明不影响主流程
✅ **详细的统计信息**：帮助评估转换质量

无论 FunASR 生成成功或失败，主要的转录流程都不会受到影响。
