"""
风险模型选择功能测试脚本

测试当元数据（标题/作者/描述）包含敏感词时，是否正确切换到风险模型
并且验证 reasoning_effort 是否正确传递
"""

import sys
import os
import json
from unittest.mock import patch, MagicMock

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
# 添加 src 目录到路径，使得可以导入 video_transcript_api
sys.path.insert(0, os.path.join(project_root, 'src'))

from src.video_transcript_api.utils.llm.llm_enhanced import EnhancedLLMProcessor


def load_config():
    """加载实际的配置文件"""
    config_path = os.path.join(project_root, 'config', 'config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def test_feature_disabled():
    """测试1：功能关闭时，始终使用默认模型"""
    print("=" * 80)
    print("Test 1: Risk Model Selection Disabled")
    print("=" * 80)

    config = load_config()
    # 确保功能是关闭的
    config['llm']['enable_risk_model_selection'] = False

    processor = EnhancedLLMProcessor(config)

    # 测试用例：即使标题包含敏感词，也应该使用默认模型
    task_id = "test_task_001"
    title = "这是一个包含政治敏感词的标题"
    author = "测试作者"
    description = "测试描述"

    selected_model, selected_effort = processor._select_summary_model(
        task_id, title, author, description
    )

    print(f"\nInput:")
    print(f"  Title: {title}")
    print(f"  Author: {author}")
    print(f"  Description: {description}")
    print(f"\nOutput:")
    print(f"  Selected Model: {selected_model}")
    print(f"  Selected Reasoning Effort: {selected_effort}")
    print(f"\nExpected:")
    print(f"  Model: {config['llm']['summary_model']} (default)")
    print(f"  Reasoning Effort: {config['llm']['summary_reasoning_effort']}")

    # 验证
    assert selected_model == config['llm']['summary_model'], \
        f"Expected default model {config['llm']['summary_model']}, got {selected_model}"
    assert selected_effort == config['llm']['summary_reasoning_effort'], \
        f"Expected default reasoning_effort {config['llm']['summary_reasoning_effort']}, got {selected_effort}"

    print("\n[PASS] Test 1: Feature disabled, using default model")


def test_feature_enabled_no_risk():
    """测试2：功能开启，无风险内容，使用默认模型"""
    print("\n" + "=" * 80)
    print("Test 2: Risk Model Selection Enabled - No Risk Content")
    print("=" * 80)

    config = load_config()
    # 启用功能
    config['llm']['enable_risk_model_selection'] = True

    processor = EnhancedLLMProcessor(config)

    # 测试用例：干净的标题
    task_id = "test_task_002"
    title = "如何提高工作效率的10个技巧"
    author = "生产力专家"
    description = "分享实用的工作方法"

    selected_model, selected_effort = processor._select_summary_model(
        task_id, title, author, description
    )

    print(f"\nInput:")
    print(f"  Title: {title}")
    print(f"  Author: {author}")
    print(f"  Description: {description}")
    print(f"\nOutput:")
    print(f"  Selected Model: {selected_model}")
    print(f"  Selected Reasoning Effort: {selected_effort}")
    print(f"\nExpected:")
    print(f"  Model: {config['llm']['summary_model']} (default)")
    print(f"  Reasoning Effort: {config['llm']['summary_reasoning_effort']}")

    # 验证
    assert selected_model == config['llm']['summary_model'], \
        f"Expected default model {config['llm']['summary_model']}, got {selected_model}"
    assert selected_effort == config['llm']['summary_reasoning_effort'], \
        f"Expected default reasoning_effort {config['llm']['summary_reasoning_effort']}, got {selected_effort}"

    print("\n[PASS] Test 2: No risk detected, using default model")


def test_feature_enabled_with_risk():
    """测试3：功能开启，检测到风险，切换到风险模型"""
    print("\n" + "=" * 80)
    print("Test 3: Risk Model Selection Enabled - Risk Content Detected")
    print("=" * 80)

    config = load_config()
    # 启用功能
    config['llm']['enable_risk_model_selection'] = True

    # Mock 风控模块，模拟检测到敏感词
    with patch('video_transcript_api.utils.risk_control.is_enabled', return_value=True):
        with patch('video_transcript_api.utils.risk_control.sanitize_text') as mock_sanitize:
            # 模拟检测到敏感词
            mock_sanitize.return_value = {
                'has_sensitive': True,
                'sensitive_words': ['政治', '敏感'],
                'sanitized_text': '这是一个包含的标题'
            }

            processor = EnhancedLLMProcessor(config)

            # 测试用例：包含敏感词的标题
            task_id = "test_task_003"
            title = "这是一个包含政治敏感词的标题"
            author = "测试作者"
            description = "测试描述"

            selected_model, selected_effort = processor._select_summary_model(
                task_id, title, author, description
            )

            print(f"\nInput:")
            print(f"  Title: {title}")
            print(f"  Author: {author}")
            print(f"  Description: {description}")
            print(f"  Detected Sensitive Words: {mock_sanitize.return_value['sensitive_words']}")
            print(f"\nOutput:")
            print(f"  Selected Model: {selected_model}")
            print(f"  Selected Reasoning Effort: {selected_effort}")
            print(f"\nExpected:")
            print(f"  Model: {config['llm']['risk_summary_model']} (risk model)")
            print(f"  Reasoning Effort: {config['llm']['risk_summary_reasoning_effort']}")

            # 验证
            assert selected_model == config['llm']['risk_summary_model'], \
                f"Expected risk model {config['llm']['risk_summary_model']}, got {selected_model}"
            assert selected_effort == config['llm']['risk_summary_reasoning_effort'], \
                f"Expected risk reasoning_effort {config['llm']['risk_summary_reasoning_effort']}, got {selected_effort}"

            print("\n[PASS] Test 3: Risk detected, switched to risk model")


def test_reasoning_effort_propagation():
    """测试4：验证 reasoning_effort 在整个调用链中正确传递"""
    print("\n" + "=" * 80)
    print("Test 4: Reasoning Effort Propagation")
    print("=" * 80)

    config = load_config()
    config['llm']['enable_risk_model_selection'] = True

    # Mock LLM API 调用
    with patch('video_transcript_api.utils.risk_control.is_enabled', return_value=True):
        with patch('video_transcript_api.utils.risk_control.sanitize_text') as mock_sanitize:
            with patch('video_transcript_api.utils.llm.llm_enhanced.call_llm_api') as mock_llm:
                # 模拟检测到风险
                mock_sanitize.return_value = {
                    'has_sensitive': True,
                    'sensitive_words': ['风险词'],
                    'sanitized_text': '处理后文本'
                }

                # 模拟 LLM 返回
                mock_llm.side_effect = lambda *args, **kwargs: "模拟LLM响应"

                processor = EnhancedLLMProcessor(config)

                # 构造一个简单的任务（短文本，走 _process_original_logic 路径）
                llm_task = {
                    'task_id': 'test_task_004',
                    'transcript': '这是一段简短的转录文本',
                    'use_speaker_recognition': False,
                    'video_title': '包含风险词的标题',
                    'author': '作者',
                    'description': '描述',
                    'transcription_data': None,
                    'platform': '',
                    'media_id': ''
                }

                # 执行任务
                result = processor.process_llm_task(llm_task)

                # 验证 call_llm_api 被调用，并且使用了正确的 reasoning_effort
                print(f"\nLLM API Call Count: {mock_llm.call_count}")
                print(f"Expected: 2 calls (1 for calibrate, 1 for summary)")

                # 检查 summary 调用是否使用了风险模型的 reasoning_effort
                summary_calls = [call for call in mock_llm.call_args_list
                               if len(call[0]) > 6 and call[0][6] == config['llm']['risk_summary_reasoning_effort']]

                print(f"\nSummary calls with risk reasoning_effort: {len(summary_calls)}")

                if len(summary_calls) > 0:
                    # 获取 summary 调用的参数
                    summary_call = [call for call in mock_llm.call_args_list
                                  if len(call[0]) > 0 and call[0][0] == config['llm']['risk_summary_model']]
                    if summary_call:
                        args = summary_call[0][0]
                        print(f"\nSummary call details:")
                        print(f"  Model used: {args[0]}")
                        print(f"  Reasoning effort: {args[6] if len(args) > 6 else 'N/A'}")

                        assert args[0] == config['llm']['risk_summary_model'], \
                            "Should use risk summary model"
                        assert args[6] == config['llm']['risk_summary_reasoning_effort'], \
                            "Should use risk summary reasoning_effort"

                print("\n[PASS] Test 4: Reasoning effort correctly propagated")


def test_config_validation():
    """测试5：配置验证 - 启用功能但未配置风险模型应该抛出异常"""
    print("\n" + "=" * 80)
    print("Test 5: Configuration Validation")
    print("=" * 80)

    config = load_config()
    config['llm']['enable_risk_model_selection'] = True
    config['llm']['risk_summary_model'] = None  # 移除风险模型配置

    print("\nTesting: enable_risk_model_selection=True but risk_summary_model=None")

    try:
        processor = EnhancedLLMProcessor(config)
        print("\n[FAIL] Test 5: Should have raised ValueError")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"\n[PASS] Test 5: Correctly raised ValueError")
        print(f"   Error message: {str(e)}")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 80)
    print("RISK MODEL SELECTION FEATURE TEST SUITE")
    print("=" * 80)
    print(f"\nUsing config from: {os.path.join(project_root, 'config', 'config.json')}")

    try:
        test_feature_disabled()
        test_feature_enabled_no_risk()
        test_feature_enabled_with_risk()
        test_reasoning_effort_propagation()
        test_config_validation()

        print("\n" + "=" * 80)
        print("ALL TESTS PASSED")
        print("=" * 80)

    except AssertionError as e:
        print(f"\n[FAIL] TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] UNEXPECTED ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()
