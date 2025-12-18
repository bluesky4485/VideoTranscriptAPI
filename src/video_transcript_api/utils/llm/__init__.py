"""
LLM 处理工具模块

包含 LLM API 调用、结构化校对、分段处理、说话人映射等功能。
"""
from .llm import (
    call_llm_api,
    set_default_config,
    get_default_config,
    StructuredResult,
    LLMStats,
    get_llm_stats,
    reset_llm_stats,
    log_llm_stats,
)
from .llm_enhanced import EnhancedLLMProcessor
from .llm_segmented import SegmentedLLMProcessor
from .structured_calibrator import StructuredCalibrator
from .text_segmentation import TextSegmentationProcessor
from .speaker_mapping import SpeakerMappingInference, infer_speaker_mapping_from_cache
from .schemas import (
    CALIBRATION_RESULT_SCHEMA,
    VALIDATION_RESULT_SCHEMA,
    SPEAKER_MAPPING_SCHEMA,
)

__all__ = [
    # LLM API
    "call_llm_api",
    "set_default_config",
    "get_default_config",
    "StructuredResult",
    "LLMStats",
    "get_llm_stats",
    "reset_llm_stats",
    "log_llm_stats",
    # Processors
    "EnhancedLLMProcessor",
    "SegmentedLLMProcessor",
    "StructuredCalibrator",
    "TextSegmentationProcessor",
    "SpeakerMappingInference",
    "infer_speaker_mapping_from_cache",
    # Schemas
    "CALIBRATION_RESULT_SCHEMA",
    "VALIDATION_RESULT_SCHEMA",
    "SPEAKER_MAPPING_SCHEMA",
]
