import sys
import os

# 添加项目根目录到路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from src.video_transcript_api.utils.dialog_renderer import DialogRenderer, render_transcript_content

def test_dialog_detection():
    """测试对话检测功能"""
    renderer = DialogRenderer()
    
    # 测试多人对话文本
    dialog_text = """知白：嗯，欢迎来到知行小酒馆，这是一档有知有行出品的播客节目。
少楠：承认自己是弱者，不是自我否定，反而能让人活得更有生命力。
知白：这是中年危机的一种褒义的说法。"""
    
    assert renderer.detect_dialog_mode(dialog_text) == True
    
    # 测试普通文本
    normal_text = """这是一段普通的文本内容，没有说话人标识。
它包含多个段落，但不是对话格式。
这种文本应该被识别为普通模式。"""
    
    assert renderer.detect_dialog_mode(normal_text) == False

def test_dialog_parsing():
    """测试对话解析功能"""
    renderer = DialogRenderer()
    
    dialog_text = """知白：欢迎来到小酒馆。
少楠：很高兴来到这里。
知白：今天我们聊什么？"""
    
    dialogs = renderer.parse_dialog_content(dialog_text)
    
    assert len(dialogs) == 3
    assert dialogs[0]['speaker'] == '知白'
    assert dialogs[0]['content'] == '欢迎来到小酒馆。'
    assert dialogs[1]['speaker'] == '少楠'
    assert dialogs[1]['content'] == '很高兴来到这里。'

def test_html_rendering():
    """测试HTML渲染功能"""
    # 测试对话渲染
    dialog_text = """知白：欢迎大家。
少楠：谢谢邀请。"""
    
    html = render_transcript_content(dialog_text)
    
    assert 'dialog-container' in html
    assert 'speaker-tag' in html
    assert '知白' in html
    assert '少楠' in html
    
    # 测试普通文本渲染
    normal_text = """这是普通文本。
包含多个段落。"""
    
    html = render_transcript_content(normal_text)
    
    assert '<p>' in html
    assert 'dialog-container' not in html

def test_speaker_colors():
    """测试说话人颜色分配"""
    renderer = DialogRenderer()
    
    speakers = ['知白', '少楠', '主持人']
    
    color1 = renderer.get_speaker_color('知白', speakers)
    color2 = renderer.get_speaker_color('少楠', speakers)
    
    assert color1 != color2  # 不同说话人应该有不同颜色
    assert color1.startswith('#')  # 应该是十六进制颜色

if __name__ == "__main__":
    print("开始测试对话渲染器...")
    
    test_dialog_detection()
    print("✓ 对话检测测试通过")
    
    test_dialog_parsing() 
    print("✓ 对话解析测试通过")
    
    test_html_rendering()
    print("✓ HTML渲染测试通过")
    
    test_speaker_colors()
    print("✓ 说话人颜色测试通过")
    
    print("\n所有测试通过！ 🎉")
    
    # 演示实际输出
    print("\n=== 演示输出 ===")
    
    sample_dialog = """知白：欢迎来到知行小酒馆，这是一档有知有行出品的播客节目，我们关注投资，更关注怎样更好地生活。我是羽白。

少楠：承认自己是弱者，不是自我否定，反而能让人活得更有生命力。因为你不需要背着全能的包袱，可以更坦然地面对自己能做什么、不能做什么。

知白：这是中年危机的一种褒义的说法。"""
    
    html_output = render_transcript_content(sample_dialog)
    
    print("对话文本渲染结果：")
    print(html_output[:200] + "..." if len(html_output) > 200 else html_output)
    
    normal_text = """这是一段普通的转录文本，没有明确的说话人标识。

它可能来自单人演讲或者没有启用说话人识别功能的转录。

这种文本将使用普通段落样式进行渲染。"""
    
    html_output = render_transcript_content(normal_text)
    
    print("\n普通文本渲染结果：")
    print(html_output[:200] + "..." if len(html_output) > 200 else html_output)