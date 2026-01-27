# 分段总结功能移除记录

## 变更日期
2026-01-27

## 背景

分段总结功能在旧架构中实现，但经过实践验证后发现：
- ❌ 失去全局上下文，总结质量下降
- ❌ 多次 API 调用，增加延迟和成本
- ❌ 容易丢失段落之间的逻辑关联

因此，新架构（LLMCoordinator + SummaryProcessor）采用**整体总结策略**，直接对完整文本进行总结。

## 移除内容

### 1. Prompt 模板（`prompts/__init__.py`）
- ❌ `SEGMENT_SUMMARY_SYSTEM_PROMPT` - 分段总结的 System Prompt
- ❌ `FINAL_SUMMARY_SYSTEM_PROMPT` - 最终总结的 System Prompt
- ❌ `build_segment_summary_user_prompt()` - 构建分段总结的 User Prompt
- ❌ `build_final_summary_user_prompt()` - 构建最终总结的 User Prompt

### 2. 处理方法（`llm_segmented.py`）
- ❌ `_summarize_segmented_text()` - 分段总结的实现方法

### 3. 导出列表（`__init__.py`）
- 从模块导出中移除上述 4 个 Prompt 相关的导出

## 保留内容

### 1. `SegmentedLLMProcessor` 类
- ✅ 保留该类，因为其**校对功能**仍在旧架构中使用
- ✅ `calibrate_text_segmented()` - 分段校对功能
- ✅ `summarize_text_segmented()` - 方法名保留用于向后兼容，但内部已改为整体总结

### 2. 向后兼容说明
```python
def summarize_text_segmented(self, ...):
    """
    对文本进行单次总结（整体处理，不分段）

    注意：方法名保留 "segmented" 是为了向后兼容，
    实际上不再进行分段处理。
    """
    return self._summarize_single_text(...)
```

## 当前架构

### 新架构（主流程）
```
LLMCoordinator
    ↓
步骤1: 校对处理 → calibrated_text
    ↓
步骤2: 总结生成（整体，不分段）
    ↓
SummaryProcessor.process()
    ↓
直接调用 LLM API（传递完整文本）
```

### 旧架构（回滚用）
```
EnhancedLLMProcessor
    ↓
SegmentedLLMProcessor.summarize_text_segmented()
    ↓
_summarize_single_text()（整体总结）
```

## 迁移指南

### 如果你的代码使用了废弃的函数：

#### 方案1：使用新架构（推荐）
```python
from video_transcript_api.utils.llm import LLMCoordinator

coordinator = LLMCoordinator(config_dict=config, cache_dir=cache_dir)
result = coordinator.process(
    content=text,
    title=title,
    author=author,
    description=description,
)

summary = result.get("summary_text")
```

#### 方案2：使用旧架构（兼容）
```python
from video_transcript_api.utils.llm import SegmentedLLMProcessor

processor = SegmentedLLMProcessor(config)
# 虽然方法名叫 "segmented"，但实际是整体总结
summary = processor.summarize_text_segmented(
    text_for_summary=calibrated_text,
    title=title,
    description=description,
)
```

## 测试验证

已通过以下测试：
- ✅ 模块导入测试
- ✅ LLMCoordinator 初始化测试
- ✅ SummaryProcessor 可用性测试
- ✅ 无测试文件依赖废弃函数

## 相关文档

- [总结流程分析](./summary_flow_analysis.md)
- [LLM 重构完成报告](./refactoring_completed.md)
- [总结功能设计](./summary_feature_design.md)

## 未来扩展

如果未来需要支持超长文本（如 200K+ tokens），可以考虑：
1. 在 `SummaryProcessor` 中添加长度检测
2. 超长文本启用分段 + 合并策略
3. 普通文本保持当前的整体总结策略

```python
# 伪代码示例
if len(text) > 100000:  # 超长文本
    return self._summarize_in_chunks(text)
else:
    return self._summarize_whole(text)  # 当前策略
```

## 注意事项

1. **不要重新引入分段总结**，除非有明确的性能需求和质量保证
2. **旧架构代码保留**是为了应急回滚，不建议在新项目中使用
3. **方法名 `summarize_text_segmented`** 保留是为了向后兼容，实际行为已改变

---

**变更原因**：优化代码库，移除废弃功能，避免混淆和维护负担
**影响范围**：仅影响未使用的废弃代码，不影响主流程
**测试状态**：✅ 已验证
