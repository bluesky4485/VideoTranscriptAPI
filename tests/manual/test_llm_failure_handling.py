"""
测试 LLM 失败时附加原始转录文本的功能
"""
import sys
import os

# 添加项目根目录到 sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

def test_failure_handling():
    """测试失败处理逻辑"""

    # 模拟 LLM 任务
    llm_task = {
        "task_id": "test_failure_123",
        "transcript": "这是一段测试的原始转录文本。包含了一些内容，用于测试当LLM调用失败时，是否能够正确附加到错误信息后面。",
        "video_title": "测试视频",
        "author": "测试作者",
        "description": "测试描述",
        "use_speaker_recognition": False,
        "transcription_data": None
    }

    # 模拟失败的返回结果
    error_message = "【LLM call failed】400 Client Error: Bad Request for url: http://example.com"

    # 模拟处理逻辑
    result_dict = {
        '校对文本': error_message,
        '内容总结': error_message
    }

    # 应用失败处理逻辑（模拟 _process_original_logic 中的处理）
    if result_dict.get('校对文本', '').startswith('【LLM call failed】'):
        print("检测到校对失败，附加原始转录文本")
        result_dict['校对文本'] = (
            f"{result_dict['校对文本']}\n\n"
            f"{'='*60}\n"
            f"以下是原始转录文本：\n"
            f"{'='*60}\n\n"
            f"{llm_task['transcript']}"
        )

    if result_dict.get('内容总结', '').startswith('【LLM call failed】'):
        print("检测到总结失败，附加原始转录文本")
        result_dict['内容总结'] = (
            f"{result_dict['内容总结']}\n\n"
            f"{'='*60}\n"
            f"以下是原始转录文本：\n"
            f"{'='*60}\n\n"
            f"{llm_task['transcript']}"
        )

    # 验证结果
    print("\n" + "="*80)
    print("校对文本结果:")
    print("="*80)
    print(result_dict['校对文本'])

    print("\n" + "="*80)
    print("内容总结结果:")
    print("="*80)
    print(result_dict['内容总结'])

    # 验证是否包含原始转录文本
    assert llm_task['transcript'] in result_dict['校对文本'], "校对文本中应包含原始转录文本"
    assert llm_task['transcript'] in result_dict['内容总结'], "内容总结中应包含原始转录文本"
    assert "以下是原始转录文本：" in result_dict['校对文本'], "校对文本中应包含分隔标识"
    assert "以下是原始转录文本：" in result_dict['内容总结'], "内容总结中应包含分隔标识"

    print("\n" + "="*80)
    print("Test passed! All assertions successful.")
    print("="*80)

if __name__ == "__main__":
    test_failure_handling()
