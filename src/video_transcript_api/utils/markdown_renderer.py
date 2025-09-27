import markdown
import pymdownx.emoji
from .logger import setup_logger

logger = setup_logger("markdown_renderer")

def _fix_indented_tables(text: str) -> str:
    """
    修复缩进的表格，让Markdown解析器能正确识别
    主要处理嵌套在列表中的表格

    Args:
        text: 原始文本

    Returns:
        str: 修复后的文本
    """
    lines = text.split('\n')
    fixed_lines = []
    in_table = False
    table_buffer = []

    for i, line in enumerate(lines):
        # 检查是否是表格行
        if '|' in line:
            stripped = line.strip()
            # 检查是否是表格分隔符行或表格内容行
            if ('---' in line or '|-' in line or
                (stripped.startswith('|') and stripped.endswith('|')) or
                (stripped.count('|') >= 2)):  # 至少包含2个|字符

                if not in_table:
                    # 开始新表格，添加空行分隔
                    if fixed_lines and fixed_lines[-1].strip():
                        fixed_lines.append('')
                    in_table = True

                # 完全移除缩进，确保表格在顶级
                table_buffer.append(stripped)
                continue

        # 如果之前在处理表格，现在遇到非表格行
        if in_table:
            # 将缓存的表格行添加到结果
            fixed_lines.extend(table_buffer)
            # 添加空行分隔表格和后续内容
            if line.strip():
                fixed_lines.append('')
            table_buffer = []
            in_table = False

        # 普通行直接添加
        fixed_lines.append(line)

    # 处理文件末尾的表格
    if in_table and table_buffer:
        fixed_lines.extend(table_buffer)

    return '\n'.join(fixed_lines)

def render_markdown_to_html(markdown_text: str) -> str:
    """
    将Markdown文本渲染为HTML
    支持表格、代码高亮、emoji等
    
    Args:
        markdown_text: Markdown文本
        
    Returns:
        str: 渲染后的HTML
    """
    try:
        # 类型安全检查：确保输入是字符串
        if markdown_text is None:
            return ""
        
        if not isinstance(markdown_text, str):
            logger.warning(f"输入类型不是字符串，而是 {type(markdown_text)}，尝试转换为字符串")
            # 如果是字典，尝试提取合适的字段
            if isinstance(markdown_text, dict):
                # 尝试提取常见的文本字段
                markdown_text = markdown_text.get('text') or markdown_text.get('content') or str(markdown_text)
            else:
                markdown_text = str(markdown_text)
        
        if not markdown_text:
            return ""

        # 预处理：修复缩进的表格
        markdown_text = _fix_indented_tables(markdown_text)

        md = markdown.Markdown(extensions=[
            'tables',           # 表格支持
            'codehilite',       # 代码高亮
            'toc',              # 目录
            'fenced_code',      # 围栏代码块
            'pymdownx.emoji',   # Emoji支持
            'pymdownx.superfences',  # 增强代码块
            'pymdownx.betterem',     # 更好的强调
            'pymdownx.highlight',    # 语法高亮
        ], extension_configs={
            'pymdownx.emoji': {
                'emoji_index': pymdownx.emoji.gemoji,
                'emoji_generator': pymdownx.emoji.to_svg,
            },
            'codehilite': {
                'css_class': 'highlight',
                'use_pygments': False,  # 使用JavaScript高亮，避免服务器依赖
            },
            'tables': {}  # 确保表格扩展正确配置
        })
        
        html = md.convert(markdown_text)
        return html
        
    except Exception as e:
        logger.error(f"Markdown渲染失败: {e}")
        # 出错时返回原始文本，用<pre>标签包装
        return f"<pre>{markdown_text}</pre>"

def get_base_url() -> str:
    """获取外部访问基础URL"""
    from utils import load_config
    
    config = load_config()
    base_url = config.get("web", {}).get("base_url", "http://localhost:8000")
    
    return base_url.rstrip('/')