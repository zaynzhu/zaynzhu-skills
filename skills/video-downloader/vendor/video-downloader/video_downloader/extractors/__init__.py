"""
Platform extractors for video-downloader-skill.
"""

from .base import PlatformExtractor
from .bilibili import BilibiliExtractor
from .douyin import DouyinExtractor
from .tiktok import TikTokExtractor

__all__ = ["PlatformExtractor", "BilibiliExtractor", "DouyinExtractor", "TikTokExtractor"]
