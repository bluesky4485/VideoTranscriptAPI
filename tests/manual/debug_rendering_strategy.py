#!/usr/bin/env python3
"""
调试渲染策略选择
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from video_transcript_api.utils.rendering import DialogRenderer
from video_transcript_api.utils.cache import analyze_cache_capabilities

def main():
    print("=== 调试渲染策略选择 ===\n")

    cache_dir = r"D:\MyFolders\Developments\0Python\250427_VideoTranscriptApi\data\cache\bilibili\2025\202509\BV14AnVznEMp"

    if not os.path.exists(cache_dir):
        print(f"缓存目录不存在: {cache_dir}")
        return

    # 分析缓存能力
    capabilities = analyze_cache_capabilities(cache_dir)

    print("缓存能力分析:")
    print(f"  has_structured_output: {capabilities.has_structured_output}")
    print(f"  has_speaker_data: {capabilities.has_speaker_data}")
    print(f"  files_present: {capabilities.files_present}")
    print(f"  speaker_count: {getattr(capabilities, 'speaker_count', 'N/A')}")

    # 获取渲染策略
    renderer = DialogRenderer()
    strategy = renderer._get_optimal_rendering_strategy(capabilities)

    print(f"\n选择的渲染策略: {strategy}")

    # 测试各个渲染方法
    if strategy == 'structured':
        print("\n测试结构化渲染:")
        try:
            result = renderer._render_from_structured_data(cache_dir)
            if result:
                print(f"结果长度: {len(result)}")
                if '<table>' in result:
                    print("包含表格标签 - 成功!")
                else:
                    print("不包含表格标签 - 失败!")
                    if '|' in result:
                        print("但包含原始表格标记")
            else:
                print("返回空结果")
        except Exception as e:
            print(f"结构化渲染失败: {e}")

    elif strategy == 'mapped':
        print("\n测试映射渲染:")
        try:
            result = renderer._render_from_speaker_mapping(cache_dir)
            if result:
                print(f"结果长度: {len(result)}")
                if '<table>' in result:
                    print("包含表格标签 - 成功!")
                else:
                    print("不包含表格标签 - 失败!")
                    if '|' in result:
                        print("但包含原始表格标记")
            else:
                print("返回空结果")
        except Exception as e:
            print(f"映射渲染失败: {e}")

    else:
        print("\n测试检测渲染:")
        try:
            result = renderer._render_calibrated_text_detection(cache_dir)
            if result:
                print(f"结果长度: {len(result)}")
                if '<table>' in result:
                    print("包含表格标签 - 成功!")
                else:
                    print("不包含表格标签 - 失败!")
                    if '|' in result:
                        print("但包含原始表格标记")
            else:
                print("返回空结果")
        except Exception as e:
            print(f"检测渲染失败: {e}")

    # 测试降级渲染
    print("\n测试降级渲染 (render_dialog_html):")
    calibrated_file = os.path.join(cache_dir, 'llm_calibrated.txt')
    if os.path.exists(calibrated_file):
        with open(calibrated_file, 'r', encoding='utf-8') as f:
            content = f.read()

        try:
            result = renderer.render_dialog_html(content)
            if result:
                print(f"结果长度: {len(result)}")
                if '<table>' in result:
                    print("包含表格标签 - 成功!")
                else:
                    print("不包含表格标签 - 失败!")
                    if '|' in result:
                        print("但包含原始表格标记")

                        # 查看检测到的内容类型
                        is_dialog = renderer.detect_dialog_mode(content)
                        print(f"检测为对话模式: {is_dialog}")

                        if not is_dialog:
                            print("被识别为普通文本，应该使用Markdown渲染")
            else:
                print("返回空结果")
        except Exception as e:
            print(f"render_dialog_html失败: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
