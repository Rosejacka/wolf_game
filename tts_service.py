"""
TTS (Text-to-Speech) 服务模块
使用 OpenAI TTS API 将文本转换为语音
"""

import os
import hashlib
import json
import random
from pathlib import Path
from openai import OpenAI
from typing import Optional, Dict, Any, List, Union
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TTSService:
    """TTS服务类，负责文本转语音功能"""
    
    def __init__(self, config_path: str = "config.json"):
        """
        初始化TTS服务
        
        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.client = None
        self.audio_cache_dir = Path("public/audio_cache")
        self.audio_cache_dir.mkdir(exist_ok=True)
        
        # 初始化OpenAI客户端
        self._init_openai_client()
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config
        except FileNotFoundError:
            logger.warning(f"配置文件 {config_path} 不存在，使用默认配置")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"配置文件格式错误: {e}")
            return {}
    
    def _init_openai_client(self):
        """初始化OpenAI客户端"""
        try:
            # 从配置文件或环境变量获取API密钥
            api_key = self.config.get('openai_api_key') or os.getenv('OPENAI_API_KEY')
            if not api_key:
                logger.error("未找到OpenAI API密钥，请在config.json中设置openai_api_key或设置OPENAI_API_KEY环境变量")
                return
                
            # 获取API基础URL（如果有自定义的话）
            base_url = self.config.get('openai_base_url') or os.getenv('OPENAI_BASE_URL')
            
            if base_url:
                self.client = OpenAI(api_key=api_key, base_url=base_url)
            else:
                self.client = OpenAI(api_key=api_key)
                
            logger.info("OpenAI TTS客户端初始化成功")
            
        except Exception as e:
            logger.error(f"初始化OpenAI客户端失败: {e}")
            self.client = None
    
    def _generate_cache_key(self, text: str, voice: str, model: str) -> str:
        """生成缓存键"""
        content = f"{text}_{voice}_{model}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """获取缓存文件路径"""
        return self.audio_cache_dir / f"{cache_key}.mp3"

    def _get_random_voice(self) -> str:
        """
        从配置中获取随机音色

        Returns:
            随机选择的音色名称
        """
        voices_config = self.config.get('comment_tts_voices', 'coral')

        # 如果配置是列表，随机选择一个
        if isinstance(voices_config, list) and voices_config:
            selected_voice = random.choice(voices_config)
            logger.info(f"随机选择音色: {selected_voice}")
            return selected_voice
        # 如果配置是字符串，直接返回
        elif isinstance(voices_config, str):
            return voices_config
        # 默认音色
        else:
            logger.warning("音色配置格式错误，使用默认音色 coral")
            return 'coral'
    
    def generate_speech(
        self,
        text: str,
        voice: Optional[str] = None,
        model: str = "tts-1",
        use_cache: bool = True
    ) -> Optional[str]:
        """
        生成语音文件
        
        Args:
            text: 要转换的文本
            voice: 语音类型 (alloy, echo, fable, onyx, nova, shimmer, coral)
            model: TTS模型 (tts-1, tts-1-hd)
            use_cache: 是否使用缓存
            
        Returns:
            生成的音频文件路径（相对于public目录），失败返回None
        """
        if not self.client:
            logger.error("OpenAI客户端未初始化")
            return None

        if not text or not text.strip():
            logger.warning("文本内容为空")
            return None

        # 如果没有指定音色，使用随机音色
        if voice is None:
            voice = self._get_random_voice()

        # 从配置获取模型（如果配置中有的话）
        if model == "tts-1":  # 只有在使用默认模型时才从配置读取
            model = self.config.get('comment_tts_models', 'tts-1')
        
        # 清理文本，移除特殊字符
        cleaned_text = self._clean_text(text)
        if not cleaned_text:
            logger.warning("清理后的文本为空")
            return None
        
        # 检查缓存
        cache_key = self._generate_cache_key(cleaned_text, voice, model)
        cache_path = self._get_cache_path(cache_key)
        
        if use_cache and cache_path.exists():
            logger.info(f"使用缓存的音频文件: {cache_path}")
            # 返回相对于public目录的路径
            return f"audio_cache/{cache_key}.mp3"
        
        try:
            logger.info(f"生成TTS音频: {cleaned_text[:50]}...")
            
            # 调用OpenAI TTS API
            with self.client.audio.speech.with_streaming_response.create(
                model=model,
                voice=voice,
                input=cleaned_text,
                response_format="mp3"
            ) as response:
                # 保存音频文件
                response.stream_to_file(cache_path)
                
            logger.info(f"TTS音频生成成功: {cache_path}")
            
            # 返回相对于public目录的路径
            return f"audio_cache/{cache_key}.mp3"
            
        except Exception as e:
            logger.error(f"生成TTS音频失败: {e}")
            return None
    
    def _clean_text(self, text: str) -> str:
        """
        清理文本，移除不适合TTS的内容
        
        Args:
            text: 原始文本
            
        Returns:
            清理后的文本
        """
        if not text:
            return ""
        
        # 移除HTML标签
        import re
        text = re.sub(r'<[^>]+>', '', text)
        
        # 移除特殊标记
        text = re.sub(r'<按回车键继续>', '', text)
        
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text).strip()
        
        # 限制文本长度（OpenAI TTS有长度限制）
        max_length = 4000  # OpenAI TTS的最大长度限制
        if len(text) > max_length:
            text = text[:max_length]
            logger.warning(f"文本过长，已截断到{max_length}字符")
        
        return text
    
    def is_available(self) -> bool:
        """检查TTS服务是否可用"""
        return self.client is not None
    
    def clear_cache(self) -> int:
        """
        清理音频缓存
        
        Returns:
            删除的文件数量
        """
        deleted_count = 0
        try:
            for audio_file in self.audio_cache_dir.glob("*.mp3"):
                audio_file.unlink()
                deleted_count += 1
            logger.info(f"清理了 {deleted_count} 个缓存音频文件")
        except Exception as e:
            logger.error(f"清理缓存失败: {e}")
        
        return deleted_count

# 全局TTS服务实例
tts_service = TTSService()
