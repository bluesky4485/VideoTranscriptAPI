import re
from typing import List, Dict, Tuple, Optional
from .logger import setup_logger

logger = setup_logger("dialog_renderer")

class DialogRenderer:
    """
    对话内容渲染器
    支持两种模式：
    1. 多人对话模式：自动检测说话人，应用对话样式
    2. 普通文本模式：无说话人识别，使用常规样式
    """
    
    # 现代美观的说话人颜色系统
    SPEAKER_COLORS = [
        '#3B82F6',  # 现代蓝
        '#10B981',  # 翡翠绿  
        '#8B5CF6',  # 紫罗兰
        '#F59E0B',  # 琥珀黄
        '#EF4444',  # 珊瑚红
        '#06B6D4',  # 天青色
        '#84CC16',  # 青柠绿
        '#F97316',  # 橙色
    ]
    
    def __init__(self):
        """初始化对话渲染器"""
        # 说话人检测的正则模式
        self.speaker_patterns = [
            r'^([^：:]+)[：:](.+)$',  # 标准格式：姓名：内容
            r'^([^：:]+)说[：:](.+)$',  # 变体格式：姓名说：内容
        ]
        
    def detect_dialog_mode(self, text: str) -> bool:
        """
        检测文本是否为多人对话格式
        
        Args:
            text: 输入文本
            
        Returns:
            bool: True表示多人对话，False表示普通文本
        """
        if not text or not isinstance(text, str):
            return False
            
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        if len(lines) < 2:
            return False
        
        # 检测包含说话人标识的行数
        dialog_lines = 0
        speakers = set()
        
        for line in lines:
            for pattern in self.speaker_patterns:
                match = re.match(pattern, line)
                if match:
                    speaker_name = match.group(1).strip()
                    if speaker_name and len(speaker_name) <= 20:  # 合理的姓名长度限制
                        speakers.add(speaker_name)
                        dialog_lines += 1
                        break
        
        # 判断标准：
        # 1. 至少有2个不同的说话人
        # 2. 至少30%的行包含说话人标识
        return (len(speakers) >= 2 and 
                dialog_lines >= max(2, len(lines) * 0.3))
    
    def parse_dialog_content(self, text: str) -> List[Dict[str, str]]:
        """
        解析多人对话内容
        
        Args:
            text: 对话文本
            
        Returns:
            List[Dict]: 解析后的对话列表，每个元素包含speaker和content
        """
        if not text:
            return []
            
        lines = text.split('\n')
        dialogs = []
        current_speaker = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_content:
                    current_content.append('')  # 保持空行
                continue
            
            # 尝试匹配说话人模式
            speaker_match = None
            for pattern in self.speaker_patterns:
                match = re.match(pattern, line)
                if match:
                    speaker_match = match
                    break
            
            if speaker_match:
                # 保存前一个说话人的内容
                if current_speaker and current_content:
                    content = '\n'.join(current_content).strip()
                    if content:
                        dialogs.append({
                            'speaker': current_speaker,
                            'content': content
                        })
                
                # 开始新的说话人
                current_speaker = speaker_match.group(1).strip()
                current_content = [speaker_match.group(2).strip()]
            else:
                # 继续当前说话人的内容
                if current_speaker:
                    current_content.append(line)
                else:
                    # 没有说话人的内容，作为第一个说话人处理
                    if not dialogs:
                        current_speaker = "内容"  # 默认说话人
                        current_content = [line]
        
        # 保存最后一个说话人的内容
        if current_speaker and current_content:
            content = '\n'.join(current_content).strip()
            if content:
                dialogs.append({
                    'speaker': current_speaker,
                    'content': content
                })
        
        return dialogs
    
    def get_speaker_color(self, speaker: str, speaker_list: List[str]) -> str:
        """
        获取说话人的颜色
        
        Args:
            speaker: 说话人姓名
            speaker_list: 所有说话人列表
            
        Returns:
            str: 十六进制颜色代码
        """
        try:
            index = speaker_list.index(speaker)
            return self.SPEAKER_COLORS[index % len(self.SPEAKER_COLORS)]
        except ValueError:
            return self.SPEAKER_COLORS[0]  # 默认颜色
    
    def render_dialog_html(self, text: str) -> str:
        """
        渲染对话为HTML格式
        
        Args:
            text: 输入文本
            
        Returns:
            str: 渲染后的HTML
        """
        try:
            # 检测是否为对话模式
            is_dialog = self.detect_dialog_mode(text)
            
            if not is_dialog:
                # 普通文本模式，使用常规段落样式
                return self._render_normal_text(text)
            
            # 多人对话模式
            dialogs = self.parse_dialog_content(text)
            if not dialogs:
                return self._render_normal_text(text)
            
            # 获取说话人列表和颜色映射
            speakers = list(dict.fromkeys([d['speaker'] for d in dialogs]))  # 保持顺序的去重
            
            html_parts = ['<div class="dialog-container">']
            
            for dialog in dialogs:
                speaker = dialog['speaker']
                content = dialog['content']
                color = self.get_speaker_color(speaker, speakers)
                
                # 处理内容中的换行
                content_html = content.replace('\n\n', '</p><p>').replace('\n', '<br>')
                if content_html and not content_html.startswith('<p>'):
                    content_html = f'<p>{content_html}</p>'
                
                html_parts.append(f'''
                <div class="dialog-item">
                    <div class="speaker-tag" style="background-color: {color};">
                        {speaker}
                    </div>
                    <div class="dialog-content">
                        {content_html}
                    </div>
                </div>
                ''')
            
            html_parts.append('</div>')
            
            return '\n'.join(html_parts)
            
        except Exception as e:
            logger.error(f"对话渲染失败: {e}")
            return self._render_normal_text(text)
    
    def _render_normal_text(self, text: str) -> str:
        """
        渲染普通文本
        
        Args:
            text: 文本内容
            
        Returns:
            str: HTML格式的文本
        """
        if not text:
            return ""
        
        # 简单的段落处理
        paragraphs = text.split('\n\n')
        html_parts = []
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if paragraph:
                # 处理单个换行为<br>，双换行为段落分隔
                paragraph_html = paragraph.replace('\n', '<br>')
                html_parts.append(f'<p>{paragraph_html}</p>')
        
        if html_parts:
            return '\n'.join(html_parts)
        else:
            return f'<p>{text.replace(chr(10), "<br>")}</p>'

def render_transcript_content(text: str) -> str:
    """
    渲染转录内容的便捷函数
    
    Args:
        text: 转录文本
        
    Returns:
        str: 渲染后的HTML
    """
    renderer = DialogRenderer()
    return renderer.render_dialog_html(text)