# 视频转录 API (Video Transcript API)

> 基于 Python 3.11+ 的异步视频转录服务，支持多平台下载、双引擎转录、智能文本处理和企业级功能集成。

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.101+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT%2B%20Commons%20Clause-yellow.svg)](LICENSE)

---

## 📋 目录

- [项目简介](#项目简介)
- [核心特性](#核心特性)
- [架构概览](#架构概览)
- [快速开始](#快速开始)
- [设计决策](#设计决策)
- [文档索引](#文档索引)
- [开发指南](#开发指南)
- [开源协议](#开源协议)

---

## 项目简介

本项目提供统一的视频/音频转录 API，支持从多个主流平台下载内容，并使用两种 ASR 引擎（CapsWriter-Offline / FunASR）进行语音识别。转录后的文本通过 LLM 进行智能校对、总结和说话人推断，同时内置缓存系统、风控机制和企业微信通知功能。

**适用场景**：
- 播客转文字
- 会议记录生成
- 视频内容索引
- 多语言字幕制作

---

## 核心特性

### 🎯 多平台支持

| 平台 | 下载方式 | 特殊能力 |
|------|---------|---------|
| **YouTube** | 原生字幕 / API 服务器 / yt-dlp | SRT 字幕、Cookie 绕过、代理下载 |
| **Bilibili** | TikHub API / BBDown | 4K 高码率、分 P 解析、付费视频 |
| **抖音** | TikHub API | 高质量 MP3、无水印流 |
| **小红书** | TikHub v3 | 分享文本、H.264 备份 URL |
| **小宇宙播客** | 网页爬虫 | JSON-LD 解析、meta 标签提取 |
| **通用链接** | 直接流式下载 | 断点续传、进度通知 |

### 🤖 双引擎转录

**CapsWriter-Offline**
- 高性能通用转录，适合批量处理
- WebSocket 实时流式传输
- 低资源消耗，快速响应

**FunASR**
- 说话人识别（Diarization）
- 时间戳和情感分析
- 适合多人对话、会议记录

### 🧠 智能文本处理

- **自动校对**：修正同音字、语法错误
- **内容总结**：生成分段摘要或核心要点
- **说话人推断**：结合元数据推断真实姓名
- **风险检测**：敏感词过滤，自动切换风险模型

### 🏗️ 企业级功能

- **智能缓存**：SQLite 元数据 + 文件系统内容，自动清理
- **多用户管理**：Bearer Token 鉴权，用户隔离
- **审计日志**：API 调用追踪、使用统计
- **企业微信通知**：任务状态实时通知
- **风控系统**：敏感词库动态加载、内容脱敏

---

## 架构概览

### 系统架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                         用户请求层                               │
├─────────────────────────────────────────────────────────────────────┤
│  FastAPI → 认证中间件 → 审计日志 → 任务队列（异步）          │
└────────────────────────┬────────────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
    ┌────▼────┐    ┌────▼────┐    ┌──▼─────────┐
    │ 下载器  │    │ 转录引擎 │    │  LLM 处理  │
    │  工厂   │    │  双队列   │    │   流水线   │
    └────┬────┘    └────┬────┘    └────┬──────┘
         │              │               │
         │              │               │
    ┌────▼──────────────▼──────────────▼────┐
    │         智能缓存系统               │
    │  (SQLite 元数据 + 文件系统)         │
    └─────────────────────────────────────┘
```

### 核心模块

| 模块 | 职责 | 技术栈 |
|------|------|---------|
| **API 服务** | FastAPI 应用、路由、依赖注入 | FastAPI, Uvicorn, Pydantic |
| **下载器** | 多平台内容获取、工厂模式 | TikHub API, yt-dlp, BeautifulSoup |
| **转录器** | 语音识别、说话人识别 | WebSocket, FFmpeg |
| **LLM 引擎** | 文本校对、总结、推断 | OpenAI 兼容 API, 结构化输出 |
| **缓存系统** | 元数据存储、文件管理 | SQLite, 文件系统 |
| **通知系统** | 企业微信消息推送 | WeComNotifier（异步） |
| **风控模块** | 敏感词检测、内容脱敏 | 动态词库、正则匹配 |

---

## 快速开始

### 环境要求

- **Python**: 3.11+
- **转录服务器**（二选一或同时部署）：
  - CapsWriter-Offline：通用转录（默认端口 6006）
  - FunASR：说话人识别（默认端口 8767）
- **依赖工具**：FFmpeg（音频处理）、uv（包管理器，推荐）

### 安装步骤

```bash
# 1. 克隆仓库
git clone <repository-url>
cd video-transcript-api

# 2. 安装 uv（如果尚未安装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. 同步依赖（自动创建虚拟环境）
uv sync

# 4. 配置服务
cp config/config.example.jsonc config/config.jsonc
# 编辑 config/config.jsonc，填写 API 密钥等配置

# 5. 启动服务
uv run python main.py --start
```

### 基本使用

```bash
# 1. 提交转录任务
curl -X POST "http://localhost:8000/api/transcribe" \
  -H "Authorization: Bearer your-auth-token" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.xiaoyuzhoufm.com/episode/687893e0a12f9ff06a98a597",
    "use_speaker_recognition": true
  }'

# 响应: {"code": 202, "message": "任务已提交", "data": {"task_id": "task_xxx", "view_token": "view_xxx"}}

# 2. 查询任务状态
curl -X GET "http://localhost:8000/api/task/task_xxx" \
  -H "Authorization: Bearer your-auth-token"

# 3. 查看结果（Web 界面）
# 访问: http://localhost:8000/view/view_xxx
```

### 运行测试

```bash
# 运行所有测试
uv run python scripts/run_tests.py

# 运行特定测试套件
uv run pytest tests/unit/
uv run pytest tests/integration/
```

---

## 设计决策

### 🚀 异步优先

**决策**：FastAPI + asyncio + 双队列架构

**原因**：
- 视频下载和网络 I/O 是阻塞操作，异步处理提升并发能力
- 转录队列和 LLM 队列分离，避免长任务阻塞短任务
- WebSocket 客户端天然适配异步模型

**实现**：
```python
async def process_task_queue():
    """转录任务队列处理器"""
    while True:
        task = await task_queue.get()
        await executor.submit(download_and_transcribe, task)

async def process_llm_queue():
    """LLM 处理队列处理器"""
    while True:
        task = await llm_queue.get()
        await llm_executor.submit(calibrate_and_summarize, task)
```

### 🏛️ 模块化设计

**决策**：工厂模式 + 依赖注入 + 领域驱动

**原因**：
- 下载器工厂简化新平台适配
- FastAPI `Depends` 实现依赖注入，便于测试
- 按业务领域拆分 utils 子包（logging/、cache/、llm/、rendering/）

**结构**：
```
api/
├── app.py              # 应用装配
├── context.py          # 依赖注入容器
├── routes/            # REST 路由
└── services/          # 业务逻辑

utils/
├── logging/           # 日志领域
├── cache/             # 缓存领域
├── llm/               # LLM 领域
└── rendering/         # 渲染领域
```

### 💾 缓存策略

**决策**：SQLite 元数据 + 文件系统内容，双层验证

**原因**：
- SQLite 支持复杂查询（按平台、时间、说话人识别筛选）
- 文件系统存储大文件（转录文本、LLM 结果）更高效
- 双层验证（数据库记录 + 文件存在）保证数据一致性

**流程**：
```python
# 查询时自动验证
result = cache_manager.get_by_url(url)
if not result or not os.path.exists(result['cache_dir']):
    cache_manager.invalidate(result['id'])
    return None  # 触发重新下载和转录
```

### 📖 文档驱动

**决策**：Docstring + Sphinx + Markdown 分离

**原因**：
- Google 风格 docstring 作为 API 的唯一真实来源（SSOT）
- Markdown 文档用于架构设计、使用指南等高层内容
- 自动生成文档站点，避免手动维护

**规范**：
```python
def calibrate_text(text: str) -> dict:
    """校对转录文本。

    Args:
        text: 原始转录文本。

    Returns:
        包含校对文本和质量评分的字典。

    Raises:
        LLMTimeoutError: LLM 调用超时。
    """
    pass
```

---

## 文档索引

项目文档中心位于 [docs/](docs/)，按用途分类：

### 📖 使用指南

- [企业微信通知配置](docs/guides/wechat_notification.md) - WeComNotifier 最佳实践
- [多用户系统配置](docs/guides/multi_user_setup.md) - 用户管理、权限控制
- [API 使用指南](docs/guides/api/) - 各平台 API 详细说明

### 🔧 开发文档

- [LLM 工程指南](docs/development/llm/engineering_guide.md) - Prompt 优化、结构化输出
- [并发处理架构](docs/development/concurrency.md) - 双队列设计、性能优化
- [风控模块开发](docs/development/risk_control.md) - 敏感词管理、审核策略
- [日志系统指南](docs/development/logging.md) - Loguru 配置、日志分析

### ✨ 功能特性

- [原始导出功能](docs/features/raw_export.md) - 原始数据导出格式
- [平台适配开发](docs/development/platforms/) - 新平台接入指南

---

## 开发指南

### 项目结构

```
video-transcript-api/
├── src/
│   ├── video_transcript_api/
│   │   ├── api/              # FastAPI 服务
│   │   ├── downloaders/       # 平台下载器
│   │   ├── transcriber/       # 转录引擎
│   │   └── utils/            # 工具模块（按领域拆分）
├── tests/                    # 测试套件
│   ├── unit/                # 单元测试
│   ├── integration/          # 集成测试
│   └── performance/          # 性能测试
├── docs/                     # 文档中心
│   ├── guides/              # 使用指南
│   ├── development/          # 开发文档
│   └── features/            # 功能特性
├── config/                   # 配置文件
├── scripts/                  # 工具脚本
└── main.py                   # 入口文件
```

### 添加新平台

1. 在 `src/video_transcript_api/downloaders/` 创建新的下载器类
2. 继承 `BaseDownloader`，实现 `can_handle()`、`get_video_info()` 等方法
3. 在 `factory.py` 中注册新下载器
4. 添加对应的测试用例

### 代码规范

- **风格**：PEP 8，4 空格缩进
- **类型提示**：使用 Python 3.11+ 类型注解
- **文档**：Google 风格 docstring
- **日志**：使用 `video_transcript_api.utils.logging.setup_logger`
- **测试**：pytest + Mock，控制台输出禁止使用中文和 emoji

### 贡献流程

1. Fork 仓库并创建特性分支
2. 遵循代码规范，编写单元测试
3. 运行 `uv run pytest tests/` 确保测试通过
4. 提交 Pull Request，描述改动内容

---

## 开源协议

本项目基于 **MIT 协议 + Commons Clause 附加条款**开源：

- ✅ 允许：非商业用途的学习、修改、分发、自用
- ❌ 禁止：售卖本软件、提供付费服务、集成到商业产品中获利

详见 [LICENSE](LICENSE) 文件。

---

## 获取帮助

- 📖 [文档中心](docs/) - 详细的使用和开发文档
- 🐛 [Issues](../../issues) - 提交 Bug 或功能请求
- 💬 [Discussions](../../discussions) - 技术讨论

---

<p align="center">
  <i>Built with ❤️ by the Video Transcript API Team</i>
</p>
