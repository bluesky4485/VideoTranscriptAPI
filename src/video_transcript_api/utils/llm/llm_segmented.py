"""
分段LLM处理模块
处理超长文本的分段校对和总结

KV Cache 优化设计：
- 静态指令放在 system_prompt 中，可被缓存复用
- 动态内容（文本、元数据）放在 user prompt 末尾
"""
import json
import os
from typing import List, Dict, Any, Optional, Tuple
from ..logging import setup_logger
from . import normalize_reasoning_effort
from .llm import call_llm_api
from .text_segmentation import TextSegmentationProcessor
from .prompts import (
    CALIBRATE_SYSTEM_PROMPT,
    CALIBRATE_SYSTEM_PROMPT_WITH_SPEAKER,
    SUMMARY_SYSTEM_PROMPT_SINGLE_SPEAKER,
    SUMMARY_SYSTEM_PROMPT_MULTI_SPEAKER,
    SEGMENT_SUMMARY_SYSTEM_PROMPT,
    FINAL_SUMMARY_SYSTEM_PROMPT,
    build_calibrate_user_prompt,
    build_summary_user_prompt,
    build_segment_summary_user_prompt,
    build_final_summary_user_prompt,
)

logger = setup_logger(__name__)


class SegmentedLLMProcessor:
    """分段LLM处理器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化分段LLM处理器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.llm_config = config.get('llm', {})
        
        # LLM API 配置 - 检查必需配置项
        required_llm_keys = ['api_key', 'base_url', 'calibrate_model', 'summary_model', 'max_retries', 'retry_delay']
        for key in required_llm_keys:
            if key not in self.llm_config:
                raise ValueError(f"配置文件中缺少 llm.{key} 配置项")
        
        self.api_key = self.llm_config['api_key']
        self.base_url = self.llm_config['base_url']
        self.calibrate_model = self.llm_config['calibrate_model']
        self.calibrate_reasoning_effort = normalize_reasoning_effort(
            self.llm_config.get('calibrate_reasoning_effort'))
        self.summary_model = self.llm_config['summary_model']
        self.summary_reasoning_effort = normalize_reasoning_effort(
            self.llm_config.get('summary_reasoning_effort'))
        self.max_retries = self.llm_config['max_retries']
        self.retry_delay = self.llm_config['retry_delay']
        
        # 初始化分段处理器
        self.segmentation_processor = TextSegmentationProcessor(config)
        
        # 并发配置
        segmentation_config = self.llm_config.get('segmentation', {})
        if 'concurrent_workers' not in segmentation_config:
            raise ValueError("配置文件中缺少 llm.segmentation.concurrent_workers 配置项")
        self.concurrent_workers = segmentation_config['concurrent_workers']
        
        logger.info(f"分段LLM处理器初始化完成，并发数: {self.concurrent_workers}")
    
    def calibrate_text_segmented(
        self,
        file_path: str,
        file_type: str,
        title: str = "",
        description: str = "",
        speaker_mapping: Optional[Dict[str, str]] = None,
        selected_calibrate_model: str = None,
        selected_calibrate_effort: str = None,
    ) -> str:
        """
        对文本进行分段校对

        Args:
            file_path: 文件路径
            file_type: 文件类型 ('txt' 或 'json')
            title: 视频标题
            description: 视频描述
            speaker_mapping: 说话人映射（可选）
            selected_calibrate_model: 选定的校对模型（可选，默认使用配置的模型）
            selected_calibrate_effort: 选定的校对 reasoning_effort（可选）

        Returns:
            校对后的完整文本
        """
        # 如果未指定模型，使用默认配置
        if selected_calibrate_model is None:
            selected_calibrate_model = self.calibrate_model
        if selected_calibrate_effort is None:
            selected_calibrate_effort = self.calibrate_reasoning_effort
        logger.info(f"开始分段校对: {os.path.basename(file_path)} (类型: {file_type}), 模型: {selected_calibrate_model}")

        try:
            if file_type == 'txt':
                return self._calibrate_txt_segmented(
                    file_path, title, description,
                    selected_calibrate_model, selected_calibrate_effort
                )
            elif file_type == 'json':
                return self._calibrate_json_segmented(
                    file_path, title, description,
                    speaker_mapping=speaker_mapping,
                    selected_calibrate_model=selected_calibrate_model,
                    selected_calibrate_effort=selected_calibrate_effort,
                )
            else:
                raise ValueError(f"不支持的文件类型: {file_type}")
        except Exception as e:
            logger.error(f"分段校对失败 {file_path}: {e}")
            return f"【分段校对失败】{e}"
    
    def _calibrate_txt_segmented(
        self, file_path: str, title: str = "", description: str = "",
        selected_calibrate_model: str = None, selected_calibrate_effort: str = None
    ) -> str:
        """
        对TXT文件进行并发分段校对

        Args:
            file_path: TXT文件路径
            title: 视频标题
            description: 视频描述
            selected_calibrate_model: 选定的校对模型
            selected_calibrate_effort: 选定的校对 reasoning_effort

        Returns:
            校对后的完整文本
        """
        # 如果未指定模型，使用默认配置
        if selected_calibrate_model is None:
            selected_calibrate_model = self.calibrate_model
        if selected_calibrate_effort is None:
            selected_calibrate_effort = self.calibrate_reasoning_effort
        import threading
        import concurrent.futures
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 分段处理
        segments = self.segmentation_processor.segment_txt_content(content)
        total_segments = len(segments)
        logger.info(f"开始并发分段校对，共 {total_segments} 个段落")
        
        # 使用线程池进行并发校对
        calibrated_segments = [None] * total_segments  # 保持原始顺序
        
        # 获取最小长度比例配置
        min_ratio = self.llm_config.get("segmentation", {}).get(
            "min_segment_ratio", self.llm_config.get("min_calibrate_ratio", 0.80)
        )

        def calibrate_segment(index, segment):
            """校对单个段落"""
            logger.info(f"开始校对第 {index+1}/{total_segments} 段 (长度: {len(segment)} 字符)")

            def run_calibration(retry_idx: int):
                # KV Cache 优化：使用静态 system_prompt + 动态 user_prompt
                retry_hint = ""
                if retry_idx > 0:
                    retry_hint = (
                        f"第 {retry_idx + 1} 次尝试：上一次校对结果长度不足，"
                        "请严格按照原文篇幅输出，必要时完整保留原文内容，只修正标点和错别字。"
                    )
                user_prompt = build_calibrate_user_prompt(
                    transcript=segment,
                    video_title=title,
                    description=description,
                    min_ratio=min_ratio,
                    retry_hint=retry_hint,
                )
                return call_llm_api(
                    model=selected_calibrate_model,
                    prompt=user_prompt,
                    api_key=self.api_key,
                    base_url=self.base_url,
                    max_retries=self.max_retries,
                    retry_delay=self.retry_delay,
                    reasoning_effort=selected_calibrate_effort,
                    task_type="calibrate_segment",
                    system_prompt=CALIBRATE_SYSTEM_PROMPT,  # KV Cache 优化：静态 system prompt
                )

            max_attempts = self.llm_config.get("segmentation", {}).get("length_retry_attempts", 3)
            calibrated_text = run_calibration(0)
            calibrated_text = self._enforce_segment_length(
                segment,
                calibrated_text,
                index,
                total_segments,
                retry_fn=run_calibration,
                max_attempts=max_attempts,
            )
            calibrated_segments[index] = calibrated_text
            logger.info(f"第 {index+1} 段校对完成（原始 {len(segment)} 字，校对 {len(calibrated_text)} 字）")
            return calibrated_text
        
        # 使用ThreadPoolExecutor进行并发处理
        max_workers = min(total_segments, self.concurrent_workers)  # 使用配置的并发数
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            futures = [
                executor.submit(calibrate_segment, i, segment) 
                for i, segment in enumerate(segments)
            ]
            
            # 等待所有任务完成
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()  # 获取结果，如果有异常会抛出
                except Exception as e:
                    logger.error(f"并发校对过程中出现错误: {e}")
        
        # 合并所有段落（按原始顺序）
        final_result = self.segmentation_processor.merge_txt_segments(calibrated_segments)
        
        logger.info(f"TXT并发分段校对完成，最终长度: {len(final_result)} 字符")
        return final_result
    
    def _calibrate_json_segmented(
        self,
        file_path: str,
        title: str,
        description: str,
        speaker_mapping: Optional[Dict[str, str]] = None,
        selected_calibrate_model: str = None,
        selected_calibrate_effort: str = None,
    ) -> str:
        """
        对JSON文件进行并发分段校对

        Args:
            file_path: JSON文件路径
            title: 视频标题
            description: 视频描述
            speaker_mapping: 说话人映射（可选）
            selected_calibrate_model: 选定的校对模型
            selected_calibrate_effort: 选定的校对 reasoning_effort

        Returns:
            校对后的完整文本
        """
        # 如果未指定模型，使用默认配置
        if selected_calibrate_model is None:
            selected_calibrate_model = self.calibrate_model
        if selected_calibrate_effort is None:
            selected_calibrate_effort = self.calibrate_reasoning_effort
        import concurrent.futures
        
        # 首先生成说话人映射
        if speaker_mapping is None:
            logger.info("生成全局说话人映射")
            speaker_mapping = self.segmentation_processor.extract_speaker_mapping_from_json(
                file_path, title, description
            )
        
        # 应用说话人映射并分段
        segments = self.segmentation_processor.segment_json_content(file_path, speaker_mapping)
        total_segments = len(segments)
        logger.info(f"开始并发分段校对，共 {total_segments} 个段落")
        
        # 使用线程池进行并发校对
        calibrated_segments = [None] * total_segments  # 保持原始顺序

        # 获取最小长度比例配置
        min_ratio = self.llm_config.get("segmentation", {}).get(
            "min_segment_ratio", self.llm_config.get("min_calibrate_ratio", 0.80)
        )

        def calibrate_json_segment(index, segment_data):
            """校对单个JSON段落"""
            segment_text = self._json_segment_to_text(segment_data)
            text_length = len(segment_text)

            logger.info(f"开始校对第 {index+1}/{total_segments} 段 (长度: {text_length} 字符)")

            def run_calibration(retry_idx: int):
                # KV Cache 优化：使用静态 system_prompt + 动态 user_prompt
                retry_hint = ""
                if retry_idx > 0:
                    retry_hint = (
                        f"第 {retry_idx + 1} 次尝试：上一次校对结果长度不足，"
                        "请严格按照原文篇幅输出，必要时完整保留原文内容，只修正标点和错别字。"
                    )
                user_prompt = build_calibrate_user_prompt(
                    transcript=segment_text,
                    video_title=title,
                    description=description,
                    min_ratio=min_ratio,
                    retry_hint=retry_hint,
                )
                return call_llm_api(
                    model=selected_calibrate_model,
                    prompt=user_prompt,
                    api_key=self.api_key,
                    base_url=self.base_url,
                    max_retries=self.max_retries,
                    retry_delay=self.retry_delay,
                    reasoning_effort=selected_calibrate_effort,
                    task_type="calibrate_segment",
                    system_prompt=CALIBRATE_SYSTEM_PROMPT_WITH_SPEAKER,  # KV Cache 优化：带说话人识别的静态 prompt
                )

            max_attempts = self.llm_config.get("segmentation", {}).get("length_retry_attempts", 3)
            calibrated_text = run_calibration(0)
            calibrated_text = self._enforce_segment_length(
                segment_text,
                calibrated_text,
                index,
                total_segments,
                retry_fn=run_calibration,
                max_attempts=max_attempts,
            )
            calibrated_segments[index] = calibrated_text
            logger.info(f"第 {index+1} 段校对完成（原始 {text_length} 字，校对 {len(calibrated_text)} 字）")
            return calibrated_text
        
        # 使用ThreadPoolExecutor进行并发处理
        max_workers = min(total_segments, self.concurrent_workers)  # 使用配置的并发数
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            futures = [
                executor.submit(calibrate_json_segment, i, segment_data) 
                for i, segment_data in enumerate(segments)
            ]
            
            # 等待所有任务完成
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()  # 获取结果，如果有异常会抛出
                except Exception as e:
                    logger.error(f"并发校对过程中出现错误: {e}")
        
        # 合并所有段落（按原始顺序）
        final_result = self.segmentation_processor.merge_json_segments(calibrated_segments)
        
        logger.info(f"JSON并发分段校对完成，最终长度: {len(final_result)} 字符")
        return final_result
    
    def _json_segment_to_text(self, segment_data: Dict[str, Any]) -> str:
        """
        将JSON段落数据转换为文本
        
        Args:
            segment_data: JSON段落数据
            
        Returns:
            格式化的文本
        """
        segments = segment_data.get('segments', [])
        text_parts = []
        
        for segment in segments:
            speaker = segment.get('speaker', '')
            text = segment.get('text', '')
            
            if speaker and text:
                text_parts.append(f"{speaker}：{text}")
            elif text:
                text_parts.append(text)
        
        return "\n\n".join(text_parts)
    
    # 注：_generate_calibrate_prompt 已移至 prompts.py 模块，使用 build_calibrate_user_prompt

    def _enforce_segment_length(
        self,
        original: str,
        calibrated: str,
        index: int,
        total_segments: int,
        retry_fn=None,
        max_attempts: int = 1,
    ) -> str:
        """确保单个分段校对结果不短于原文阈值，必要时重试"""
        if not original:
            return calibrated

        min_ratio = self.llm_config.get("segmentation", {}).get(
            "min_segment_ratio", self.llm_config.get("min_calibrate_ratio", 0.80)
        )
        min_length = int(len(original) * min_ratio)
        attempt = 1

        while True:
            calibrated_length = len(calibrated or "")
            ratio = (calibrated_length / len(original)) if original else 0
            if calibrated_length >= min_length:
                logger.info(
                    f"第 {index + 1}/{total_segments} 段校对长度满足要求：原始 {len(original)} 字，校对 {calibrated_length} 字，"
                    f"占比 {ratio * 100:.2f}%（第 {attempt} 次尝试）"
                )
                return calibrated

            if not retry_fn or attempt >= max_attempts:
                logger.warning(
                    f"第 {index + 1}/{total_segments} 段校对后长度 {ratio * 100:.2f}% 小于阈值 {min_ratio * 100:.2f}%，"
                    f"原始 {len(original)} 字，校对 {calibrated_length} 字，重试次数 {attempt}/{max_attempts}，回退原段"
                )
                return original

            logger.warning(
                f"第 {index + 1}/{total_segments} 段校对后长度 {ratio * 100:.2f}% 小于阈值 {min_ratio * 100:.2f}%，"
                f"准备进行第 {attempt + 1}/{max_attempts} 次重试"
            )
            attempt += 1
            calibrated = retry_fn(attempt - 1)
    
    def summarize_text_segmented(self, text_for_summary: str, title: str = "", description: str = "", selected_summary_model: str = None, selected_reasoning_effort: str = None) -> str:
        """
        对文本进行单次总结（不分段，文本可以是原始或校对结果）

        Args:
            text_for_summary: 用于总结的文本
            title: 视频标题
            description: 视频描述
            selected_summary_model: 选定的总结模型（如果为None则使用默认模型）
            selected_reasoning_effort: 选定的 reasoning_effort（如果为None则使用默认值）

        Returns:
            总结文本
        """
        logger.info(f"开始文本总结，长度: {len(text_for_summary)} 字符")

        # 如果未指定模型，使用默认模型
        if selected_summary_model is None:
            selected_summary_model = self.summary_model

        # 如果未指定 reasoning_effort，使用默认值
        if selected_reasoning_effort is None:
            selected_reasoning_effort = self.summary_reasoning_effort

        # 不再分段，直接对全文进行总结，让LLM有全局理解
        return self._summarize_single_text(text_for_summary, title, description, selected_summary_model, selected_reasoning_effort)
    
    def _summarize_single_text(self, text: str, title: str, description: str, selected_summary_model: str, selected_reasoning_effort: str) -> str:
        """
        对单个文本进行总结

        Args:
            text: 文本内容
            title: 视频标题
            description: 视频描述
            selected_summary_model: 选定的总结模型
            selected_reasoning_effort: 选定的 reasoning_effort

        Returns:
            总结文本
        """
        # 检测说话人数量，决定总结策略
        import re
        speaker_pattern = r'Speaker\d+'
        unique_speakers = set(re.findall(speaker_pattern, text))
        speaker_count = len(unique_speakers) if unique_speakers else 1

        logger.info(f"检测到说话人数量: {speaker_count}，选择相应的总结策略")

        # KV Cache 优化：根据说话人数量选择静态 system prompt
        if speaker_count > 1:
            system_prompt = SUMMARY_SYSTEM_PROMPT_MULTI_SPEAKER
        else:
            system_prompt = SUMMARY_SYSTEM_PROMPT_SINGLE_SPEAKER

        # 构建动态 user prompt
        user_prompt = build_summary_user_prompt(
            transcript=text,
            video_title=title,
            description=description,
        )

        # 使用选定的总结模型和 reasoning_effort
        summary = call_llm_api(
            model=selected_summary_model,
            prompt=user_prompt,
            api_key=self.api_key,
            base_url=self.base_url,
            max_retries=self.max_retries,
            retry_delay=self.retry_delay,
            reasoning_effort=selected_reasoning_effort,
            task_type="summary",
            system_prompt=system_prompt,  # KV Cache 优化：静态 system prompt
        )

        logger.info("文本总结完成")
        return summary
    
    def _summarize_segmented_text(self, text: str, title: str, description: str) -> str:
        """
        对超长文本进行分段总结

        Args:
            text: 文本内容
            title: 视频标题
            description: 视频描述

        Returns:
            总结文本
        """
        # 分段处理
        segments = self.segmentation_processor.segment_txt_content(text)
        segment_summaries = []

        total_segments = len(segments)
        logger.info(f"开始分段总结，共 {total_segments} 个段落")

        for i, segment in enumerate(segments):
            logger.info(f"正在总结第 {i+1}/{total_segments} 段")

            # KV Cache 优化：使用静态 system prompt + 动态 user prompt
            user_prompt = build_segment_summary_user_prompt(segment, i+1, total_segments)

            segment_summary = call_llm_api(
                model=self.summary_model,
                prompt=user_prompt,
                api_key=self.api_key,
                base_url=self.base_url,
                max_retries=self.max_retries,
                retry_delay=self.retry_delay,
                reasoning_effort=self.summary_reasoning_effort,
                task_type="segment_summary",
                system_prompt=SEGMENT_SUMMARY_SYSTEM_PROMPT,  # KV Cache 优化
            )

            segment_summaries.append(segment_summary)
            logger.info(f"第 {i+1} 段总结完成")

        # 将各段总结合并为最终总结
        combined_summaries = "\n\n".join(segment_summaries)

        # KV Cache 优化：使用静态 system prompt + 动态 user prompt
        final_user_prompt = build_final_summary_user_prompt(combined_summaries, title, description)

        logger.info("开始生成最终总结")
        final_summary = call_llm_api(
            model=self.summary_model,
            prompt=final_user_prompt,
            api_key=self.api_key,
            base_url=self.base_url,
            max_retries=self.max_retries,
            retry_delay=self.retry_delay,
            reasoning_effort=self.summary_reasoning_effort,
            task_type="final_summary",
            system_prompt=FINAL_SUMMARY_SYSTEM_PROMPT,  # KV Cache 优化
        )

        logger.info("分段总结完成")
        return final_summary

    # 注：以下方法已移至 prompts.py 模块：
    # - _generate_summary_prompt -> SUMMARY_SYSTEM_PROMPT_* + build_summary_user_prompt
    # - _generate_segment_summary_prompt -> SEGMENT_SUMMARY_SYSTEM_PROMPT + build_segment_summary_user_prompt
    # - _generate_final_summary_prompt -> FINAL_SUMMARY_SYSTEM_PROMPT + build_final_summary_user_prompt
