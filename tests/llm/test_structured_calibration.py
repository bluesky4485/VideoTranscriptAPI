"""
测试结构化校对功能
"""
import os
import sys
import json
import unittest
from unittest.mock import patch, MagicMock

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from video_transcript_api.utils.llm import StructuredCalibrator, EnhancedLLMProcessor
from video_transcript_api.utils.logging import load_config


class TestStructuredCalibration(unittest.TestCase):
    """测试结构化校对功能"""
    
    def setUp(self):
        """设置测试环境"""
        # 加载配置
        self.config = load_config()
        
        # 创建测试数据
        self.test_funasr_data = {
            "segments": [
                {
                    "spk": "spk0",
                    "text": "那个呃今天我们来聊一下产品设计呃我觉得这个很重要的",
                    "start": 10.5,
                    "end": 15.2
                },
                {
                    "spk": "spk1", 
                    "text": "对对对我也这么认为呃我觉得用户体验是最核心的",
                    "start": 15.8,
                    "end": 20.1
                },
                {
                    "spk": "spk0",
                    "text": "是的是的然后我们需要考虑用户的真实需求",
                    "start": 20.5,
                    "end": 24.3
                }
            ],
            "speakers": ["spk0", "spk1"]
        }
        
        self.test_video_metadata = {
            "video_title": "产品设计对谈",
            "author": "设计师频道", 
            "description": "两位资深产品设计师分享他们的设计理念和实践经验"
        }
        
        self.test_speaker_mapping = {
            "spk0": "知白",
            "spk1": "少楠"
        }
    
    def test_extract_time_enhanced_dialogs(self):
        """测试提取带时间信息的对话"""
        dialogs = StructuredCalibrator.extract_time_enhanced_dialogs_from_funasr(
            self.test_funasr_data, 
            self.test_speaker_mapping
        )
        
        # 验证结果
        self.assertEqual(len(dialogs), 3)  # spk0->spk1->spk0，不连续，所以是3个对话
        
        # 验证第一个对话
        first_dialog = dialogs[0]
        self.assertEqual(first_dialog['speaker'], '知白')
        self.assertEqual(first_dialog['start_time'], '00:00:10')
        self.assertIn('产品设计', first_dialog['text'])
        
        # 验证第二个对话
        second_dialog = dialogs[1]
        self.assertEqual(second_dialog['speaker'], '少楠')
        self.assertEqual(second_dialog['start_time'], '00:00:15')
        self.assertIn('用户体验', second_dialog['text'])
        
        # 验证第三个对话
        third_dialog = dialogs[2]
        self.assertEqual(third_dialog['speaker'], '知白')
        self.assertEqual(third_dialog['start_time'], '00:00:20')
        self.assertIn('用户的真实需求', third_dialog['text'])
        
        print("时间信息提取测试通过")
    
    def test_intelligent_chunking(self):
        """测试智能分块功能"""
        calibrator = StructuredCalibrator(self.config)
        
        # 创建测试对话
        test_dialogs = [
            {
                'speaker': '知白',
                'text': '短对话',
                'start_time': '00:00:10',
                'duration': 5
            },
            {
                'speaker': '少楠', 
                'text': '这是一个稍微长一点的对话，包含更多的内容和细节' * 10,  # 长对话
                'start_time': '00:00:15',
                'duration': 10
            },
            {
                'speaker': '知白',
                'text': '另一个短对话',
                'start_time': '00:00:25', 
                'duration': 3
            }
        ]
        
        chunks = calibrator._intelligent_chunking(test_dialogs)
        
        # 验证分块结果
        self.assertGreater(len(chunks), 0)
        print(f"分块测试通过，共生成 {len(chunks)} 个chunk")
        
        for i, chunk in enumerate(chunks):
            chunk_length = sum(len(dialog.get('text', '')) for dialog in chunk)
            print(f"  Chunk {i+1}: {len(chunk)} 个对话，总长度 {chunk_length} 字符")
    
    @patch('video_transcript_api.utils.llm.call_llm_api')
    def test_calibration_process(self, mock_llm_call):
        """测试校对流程"""
        # 模拟LLM响应
        mock_calibration_response = """```json
{
  "calibrated_dialogs": [
    {
      "start_time": "00:00:10",
      "speaker": "知白",
      "text": "今天我们来聊一下产品设计，我觉得这个很重要。然后我们需要考虑用户的真实需求。"
    },
    {
      "start_time": "00:00:15", 
      "speaker": "少楠",
      "text": "对，我也这么认为。我觉得用户体验是最核心的。"
    }
  ]
}
```"""
        
        mock_validation_response = """```json
{
  "overall_score": 9.0,
  "scores": {
    "format_correctness": 10,
    "content_fidelity": 9,
    "text_quality": 9,
    "speaker_consistency": 10,
    "time_consistency": 10
  },
  "pass": true,
  "issues": [],
  "recommendation": "校对质量优秀"
}
```"""
        
        # 设置mock返回值（校对调用和验证调用）
        mock_llm_call.side_effect = [mock_calibration_response, mock_validation_response]
        
        calibrator = StructuredCalibrator(self.config)
        
        # 提取对话
        dialogs_with_time = StructuredCalibrator.extract_time_enhanced_dialogs_from_funasr(
            self.test_funasr_data,
            self.test_speaker_mapping
        )
        
        # 执行校对
        calibrated_dialogs = calibrator.calibrate_structured_dialogs(
            dialogs_with_time,
            self.test_video_metadata
        )
        
        # 验证结果
        self.assertEqual(len(calibrated_dialogs), 3)
        self.assertIn('今天我们来聊一下产品设计', calibrated_dialogs[0]['text'])
        self.assertEqual(calibrated_dialogs[0]['speaker'], '知白')
        
        print("校对流程测试通过")
        print(f"  校对前对话数: {len(dialogs_with_time)}")
        print(f"  校对后对话数: {len(calibrated_dialogs)}")
    
    @patch('video_transcript_api.utils.llm.call_llm_api')
    def test_enhanced_llm_processor_integration(self, mock_llm_call):
        """测试增强LLM处理器集成"""
        # 模拟所有LLM调用
        mock_responses = [
            # 说话人推断响应
            """```json
{
  "speaker_mapping": {
    "spk0": "知白",
    "spk1": "少楠"
  },
  "confidence": {
    "spk0": 0.9,
    "spk1": 0.8
  },
  "reasoning": "根据对话内容推断得出"
}
```""",
            # 校对响应
            """```json
{
  "calibrated_dialogs": [
    {
      "start_time": "00:00:10",
      "speaker": "知白",
      "text": "今天我们来聊一下产品设计，我觉得这个很重要。然后我们需要考虑用户的真实需求。"
    },
    {
      "start_time": "00:00:15",
      "speaker": "少楠", 
      "text": "对，我也这么认为。我觉得用户体验是最核心的。"
    }
  ]
}
```""",
            # 验证响应
            """```json
{
  "overall_score": 9.0,
  "scores": {
    "format_correctness": 10,
    "content_fidelity": 9,
    "text_quality": 9,
    "speaker_consistency": 10,
    "time_consistency": 10
  },
  "pass": true,
  "issues": [],
  "recommendation": "校对质量优秀"
}
```""",
            # 总结响应
            """## 1. 概述
这是一场关于产品设计的深度对话，知白和少楠两位设计师分享了他们对产品设计的理解。

## 2. 主题详述
### 产品设计的重要性
知白强调了产品设计的重要性，认为这是产品成功的关键因素。

### 用户体验核心
少楠提到用户体验是产品设计的核心，需要始终以用户为中心。

## 3. 核心观点与洞察
- 产品设计需要考虑用户的真实需求
- 用户体验是产品设计的核心要素
"""
        ]
        
        mock_llm_call.side_effect = mock_responses
        
        processor = EnhancedLLMProcessor(self.config)
        
        # 创建模拟任务
        llm_task = {
            "task_id": "test_123",
            "video_title": "产品设计对谈",
            "author": "设计师频道",
            "description": "两位资深产品设计师分享设计理念",
            "transcript": "测试转录文本",
            "use_speaker_recognition": True,
            "transcription_data": self.test_funasr_data,
            "platform": "test",
            "media_id": "test_123"
        }
        
        # 执行处理
        result = processor.process_llm_task(llm_task)
        
        # 验证结果
        self.assertIn('校对文本', result)
        self.assertIn('内容总结', result)
        self.assertIn('设计师A：', result['校对文本'])
        self.assertIn('## 1. 概述', result['内容总结'])
        
        print("增强LLM处理器集成测试通过")
    
    def test_seconds_to_timestamp(self):
        """测试时间戳转换"""
        test_cases = [
            (65, "00:01:05"),
            (3661, "01:01:01"),
            (0, "00:00:00"),
            (3600, "01:00:00")
        ]
        
        for seconds, expected in test_cases:
            result = StructuredCalibrator.seconds_to_timestamp(seconds)
            self.assertEqual(result, expected)
        
        print("时间戳转换测试通过")


def run_specific_test():
    """运行特定测试"""
    # 可以单独运行某个测试
    suite = unittest.TestSuite()
    
    # 添加要运行的测试
    suite.addTest(TestStructuredCalibration('test_extract_time_enhanced_dialogs'))
    suite.addTest(TestStructuredCalibration('test_intelligent_chunking'))
    suite.addTest(TestStructuredCalibration('test_calibration_process'))
    suite.addTest(TestStructuredCalibration('test_enhanced_llm_processor_integration'))
    suite.addTest(TestStructuredCalibration('test_seconds_to_timestamp'))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    print("开始测试结构化校对功能...")
    print("=" * 50)
    
    # 运行测试
    success = run_specific_test()
    
    print("=" * 50)
    if success:
        print("所有测试通过！结构化校对功能工作正常。")
    else:
        print("部分测试失败，请检查实现。")
        
    print("\n测试总结:")
    print("1. 时间信息提取和对话合并")
    print("2. 智能分块策略")
    print("3. 校对流程（含质量验证）")
    print("4. 增强LLM处理器集成")
    print("5. 时间戳格式转换")
    
    print("\n配置说明:")
    print("- 分块长度范围: 300-1500字符")
    print("- 并发限制: 3个worker")
    print("- 校对重试: 最多2次")
    print("- 质量阈值: 总分8.0，单项7.0")
    
    print("\n输出文件:")
    print("- llm_processed.json: 结构化数据（v2格式）")
    print("- llm_calibrated.txt: 校对后文本（兼容性）")
    print("- llm_summary.txt: 总结文本")
    print("- .format_version: 版本标识(v2)")
