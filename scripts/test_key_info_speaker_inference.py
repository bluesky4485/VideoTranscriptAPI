"""
测试 Key Info 提取和 Speaker 推断流程

使用实际的小宇宙播客转录数据进行测试
"""

import sys
import json
import json5
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from video_transcript_api.utils.llm.core.config import LLMConfig
from video_transcript_api.utils.llm.core.llm_client import LLMClient
from video_transcript_api.utils.llm.core.key_info_extractor import KeyInfoExtractor
from video_transcript_api.utils.llm.core.speaker_inferencer import SpeakerInferencer
from video_transcript_api.utils.logging import setup_logger

logger = setup_logger(__name__)


def load_config():
    """加载配置文件"""
    config_path = project_root / "config" / "config.jsonc"
    logger.info(f"Loading config from: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        return json5.load(f)


def load_transcript_data():
    """加载转录数据"""
    transcript_path = (
        project_root / "data" / "cache" / "xiaoyuzhou" / "2026" / "202601"
        / "68f7975f456ffec65ede5e47" / "transcript_funasr.json"
    )
    logger.info(f"Loading transcript from: {transcript_path}")

    with open(transcript_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_key_info_extraction(llm_client: LLMClient, config: LLMConfig):
    """测试关键信息提取"""
    logger.info("\n" + "="*80)
    logger.info("TEST 1: Key Info Extraction")
    logger.info("="*80)

    # 视频元数据
    title = "99.身边的恋人让你烦了？这期节目听完你更爱TA了！"
    author = "三立人"
    description = """本期也算是一期和听友共创的节目了，三立人在相亲交友的赛道一马狂奔之后，越来越多投稿给了我们越来越多的创作素材。大部分的甜蜜爱情都是大同小异的，但是古怪抓马的故事可是千奇百怪五花八门，本期全部案例来自于粉丝投稿，合并了同类型并且做了一些脱敏处理，大家看个乐呵不要对号入座也不要觉得都是这样的人，三立人开心最重要。

**【节目时间轴】**

01:01 怎么有人相亲还要卷证书啊？

03:05 是这样的，多得是不谈风月只谈现实的人。

05:07怎么还得整个群面啊！

07:19 我只负责把人带到，剩下的就要靠你们自己发挥了。

10:01 你可以指我，点我，但你不要对我指指点点的！

12:34 你真的很在意你就纹身上，别到时候没屁搁楞嗓子。

15:13 大家都是走个过场，甩脸子就没意思了，还是和和气气的。

17:50 人不要把自己太当回事，也不要把别人太不当回事。

23:20  产品和实物不符我可以理解，但你换个产品可不行了。

27:01 真拿我完成任务呢？

29:10 己所不欲勿施于人啊！

**【大富大贵听友群】**

进群记得加我们美女老板曼浓的微信，ID是abbyy312（备注：三立人）

也请关注我们美女老板曼浓的即刻：林曼浓

欢迎订阅并加入我们，一起开怀大笑！

**【三立人主播】**

老徐，ENFP，主业帮人找工作，副业帮人找对象。社交活动从业者，人类观察计划未完成者。没话找话一级高手。

曼浓，ENFP，音乐学院毕业的退休女歌手，曾经的销冠，现役女老板。手把手教你赚钱。

噗噗猫，ESFJ，久病成良医的知名探院博主，主业医疗相关。普通话说的极其普通。

**【本期三立人幕后】**

文案：老徐

剪辑：晚也不晚

**【诚招广告商】**

欢迎各大金主妈妈、金主爸爸与我们合作，可接置换、口播、定制与分销等。

合作微信：Rosai361204或者Missupupu（备注：合作）"""

    logger.info(f"\nInput metadata:")
    logger.info(f"  Title: {title}")
    logger.info(f"  Author: {author}")
    logger.info(f"  Description length: {len(description)} chars")
    logger.info(f"  Description preview: {description[:200]}...")

    # 创建提取器
    extractor = KeyInfoExtractor(
        llm_client=llm_client,
        cache_manager=None,  # 不使用缓存
        model=config.calibrate_model,
        reasoning_effort=config.calibrate_reasoning_effort,
    )

    # 提取关键信息
    logger.info("\nCalling KeyInfoExtractor.extract()...")
    try:
        key_info = extractor.extract(
            title=title,
            author=author,
            description=description,
            platform="xiaoyuzhou",
            media_id="68f7975f456ffec65ede5e47",
        )

        logger.info("\nKey Info Extraction Result:")
        logger.info(f"  Names: {key_info.names}")
        logger.info(f"  Places: {key_info.places}")
        logger.info(f"  Technical terms: {key_info.technical_terms}")
        logger.info(f"  Brands: {key_info.brands}")
        logger.info(f"  Abbreviations: {key_info.abbreviations}")
        logger.info(f"  Foreign terms: {key_info.foreign_terms}")
        logger.info(f"  Other entities: {key_info.other_entities}")

        return key_info

    except Exception as e:
        logger.error(f"Key info extraction failed: {e}", exc_info=True)
        return None


def test_speaker_inference(
    llm_client: LLMClient,
    config: LLMConfig,
    transcript_data: dict
):
    """测试说话人推断"""
    logger.info("\n" + "="*80)
    logger.info("TEST 2: Speaker Inference")
    logger.info("="*80)

    # 视频元数据
    title = "99.身边的恋人让你烦了？这期节目听完你更爱TA了！"
    author = "三立人"
    description = """本期也算是一期和听友共创的节目了，三立人在相亲交友的赛道一马狂奔之后，越来越多投稿给了我们越来越多的创作素材。大部分的甜蜜爱情都是大同小异的，但是古怪抓马的故事可是千奇百怪五花八门，本期全部案例来自于粉丝投稿，合并了同类型并且做了一些脱敏处理，大家看个乐呵不要对号入座也不要觉得都是这样的人，三立人开心最重要。

**【节目时间轴】**

01:01 怎么有人相亲还要卷证书啊？

03:05 是这样的，多得是不谈风月只谈现实的人。

05:07怎么还得整个群面啊！

07:19 我只负责把人带到，剩下的就要靠你们自己发挥了。

10:01 你可以指我，点我，但你不要对我指指点点的！

12:34 你真的很在意你就纹身上，别到时候没屁搁楞嗓子。

15:13 大家都是走个过场，甩脸子就没意思了，还是和和气气的。

17:50 人不要把自己太当回事，也不要把别人太不当回事。

23:20  产品和实物不符我可以理解，但你换个产品可不行了。

27:01 真拿我完成任务呢？

29:10 己所不欲勿施于人啊！

**【大富大贵听友群】**

进群记得加我们美女老板曼浓的微信，ID是abbyy312（备注：三立人）

也请关注我们美女老板曼浓的即刻：林曼浓

欢迎订阅并加入我们，一起开怀大笑！

**【三立人主播】**

老徐，ENFP，主业帮人找工作，副业帮人找对象。社交活动从业者，人类观察计划未完成者。没话找话一级高手。

曼浓，ENFP，音乐学院毕业的退休女歌手，曾经的销冠，现役女老板。手把手教你赚钱。

噗噗猫，ESFJ，久病成良医的知名探院博主，主业医疗相关。普通话说的极其普通。

**【本期三立人幕后】**

文案：老徐

剪辑：晚也不晚

**【诚招广告商】**

欢迎各大金主妈妈、金主爸爸与我们合作，可接置换、口播、定制与分销等。

合作微信：Rosai361204或者Missupupu（备注：合作）"""

    # 提取说话人和对话
    speakers = transcript_data["speakers"]
    dialogs = transcript_data["segments"]

    logger.info(f"\nInput data:")
    logger.info(f"  Title: {title}")
    logger.info(f"  Author: {author}")
    logger.info(f"  Speakers: {speakers}")
    logger.info(f"  Total dialogs: {len(dialogs)}")
    logger.info(f"  Description length: {len(description)} chars")

    # 显示前几条对话（用于验证采样效果）
    logger.info(f"\nFirst 5 dialogs:")
    for i, dialog in enumerate(dialogs[:5]):
        logger.info(f"    [{dialog['speaker']}] {dialog['text'][:50]}...")

    # 创建推断器
    inferencer = SpeakerInferencer(
        llm_client=llm_client,
        cache_manager=None,  # 不使用缓存
        model=config.calibrate_model,
        reasoning_effort=config.calibrate_reasoning_effort,
        sample_length=1000,  # 采样 1000 字符
    )

    # 推断说话人
    logger.info("\nCalling SpeakerInferencer.infer()...")
    try:
        speaker_mapping = inferencer.infer(
            speakers=speakers,
            dialogs=dialogs,
            title=title,
            author=author,
            description=description,
            key_info=None,  # 不传递 key_info
            platform="xiaoyuzhou",
            media_id="68f7975f456ffec65ede5e47",
        )

        logger.info("\nSpeaker Inference Result:")
        for speaker, name in speaker_mapping.items():
            logger.info(f"  {speaker} -> {name}")

        return speaker_mapping

    except Exception as e:
        logger.error(f"Speaker inference failed: {e}", exc_info=True)
        return None


def main():
    """主函数"""
    logger.info("Starting Key Info and Speaker Inference Test")
    logger.info("="*80)

    # 1. 加载配置
    config_dict = load_config()
    llm_config = LLMConfig.from_dict(config_dict)

    logger.info(f"\nLLM Configuration:")
    logger.info(f"  API URL: {llm_config.base_url}")
    logger.info(f"  Calibrate model: {llm_config.calibrate_model}")
    logger.info(f"  Reasoning effort: {llm_config.calibrate_reasoning_effort}")

    # 2. 创建 LLM 客户端
    llm_client = LLMClient(
        api_key=llm_config.api_key,
        base_url=llm_config.base_url,
        max_retries=llm_config.max_retries,
        retry_delay=llm_config.retry_delay,
        config=config_dict,  # 传递完整配置，包含 json_output 设置
    )

    # 3. 加载转录数据
    transcript_data = load_transcript_data()

    # 4. 测试 Key Info 提取
    key_info = test_key_info_extraction(llm_client, llm_config)

    # 5. 测试 Speaker 推断
    speaker_mapping = test_speaker_inference(llm_client, llm_config, transcript_data)

    # 6. 总结
    logger.info("\n" + "="*80)
    logger.info("TEST SUMMARY")
    logger.info("="*80)

    if key_info:
        logger.info("\nKey Info Extraction: SUCCESS")
        logger.info(f"  Expected names: ['老徐', '曼浓', '噗噗猫']")
        logger.info(f"  Actual names: {key_info.names}")

        # 检查是否包含主播名字
        expected_hosts = ["老徐", "曼浓", "噗噗猫"]
        found_hosts = [name for name in expected_hosts if name in key_info.names]
        if found_hosts:
            logger.info(f"  ✓ Found {len(found_hosts)}/{len(expected_hosts)} host names: {found_hosts}")
        else:
            logger.warning(f"  ✗ No host names found in extracted names!")
    else:
        logger.error("\nKey Info Extraction: FAILED")

    if speaker_mapping:
        logger.info("\nSpeaker Inference: SUCCESS")
        logger.info(f"  Expected mapping:")
        logger.info(f"    Speaker3 -> 老徐 (from line 16: '大家好，我是老徐')")
        logger.info(f"    Speaker2 -> 噗噗猫 (from line 22: '我是扑扑猫')")
        logger.info(f"  Actual mapping:")
        for speaker, name in speaker_mapping.items():
            logger.info(f"    {speaker} -> {name}")

        # 验证推断结果
        if "老徐" in speaker_mapping.values():
            logger.info(f"  ✓ Found '老徐' in mapping")
        else:
            logger.warning(f"  ✗ '老徐' not found in mapping")

        if "噗噗猫" in speaker_mapping.values() or "扑扑猫" in speaker_mapping.values():
            logger.info(f"  ✓ Found '噗噗猫' in mapping")
        else:
            logger.warning(f"  ✗ '噗噗猫' not found in mapping")
    else:
        logger.error("\nSpeaker Inference: FAILED")

    logger.info("\n" + "="*80)
    logger.info("Test completed")
    logger.info("="*80)


if __name__ == "__main__":
    main()
