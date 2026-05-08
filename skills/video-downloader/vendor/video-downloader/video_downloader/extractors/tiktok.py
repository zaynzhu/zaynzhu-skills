"""
TikTok platform extractor.
"""

import re
import json
import httpx
from typing import List, Optional, Dict
from ..models import VideoMetadata, QualityOption
from ..exceptions import PlatformError, VideoUnavailableError, ValidationError
from ..logger import logger
from .base import PlatformExtractor


class TikTokExtractor(PlatformExtractor):
    """
    TikTok video extractor.
    
    Supports:
    - Regular videos
    - Browser automation for anti-bot bypass
    """
    
    PLATFORM_NAME = 'tiktok'
    
    # URL patterns
    URL_PATTERNS = [
        r'https?://(?:www\.)?tiktok\.com/@[\w.-]+/video/(\d+)',
        r'https?://(?:vm|vt)\.tiktok\.com/(\w+)',  # Short URL
        r'https?://(?:www\.)?tiktok\.com/t/(\w+)',  # Short URL
    ]
    
    def __init__(self):
        """Initialize TikTok extractor."""
        super().__init__()
        logger.info("TikTokExtractor initialized")
    
    def can_handle(self, url: str) -> bool:
        """Check if this extractor can handle the URL."""
        return any(re.search(pattern, url) for pattern in self.URL_PATTERNS)
    
    def validate_url(self, url: str) -> bool:
        """Validate TikTok URL format."""
        if not self.can_handle(url):
            return False
        
        # Extract video ID
        video_id = self._extract_video_id(url)
        return video_id is not None
    
    def requires_browser_automation(self) -> bool:
        """TikTok requires browser automation for anti-bot bypass."""
        return True
    
    async def extract_metadata(
        self,
        url: str,
        cookies: Optional[Dict[str, str]] = None
    ) -> VideoMetadata:
        """
        Extract video metadata from TikTok.
        
        Args:
            url: Video URL
            cookies: Optional cookies for authentication
            
        Returns:
            VideoMetadata
        """
        logger.info(f"Extracting metadata from: {url}")
        
        # Handle short URL
        if any(pattern in url for pattern in ['vm.tiktok.com', 'vt.tiktok.com', 'tiktok.com/t/']):
            url = await self._resolve_short_url(url)
        
        # Extract video ID
        video_id = self._extract_video_id(url)
        if not video_id:
            raise ValidationError(f"Invalid TikTok URL: {url}")
        
        # Fetch video detail
        video_data = await self._fetch_video_detail(video_id, cookies)
        
        # Parse metadata
        metadata = self._parse_video_data(video_data, video_id)
        
        logger.info(f"Extracted metadata: {metadata.title}")
        return metadata
    
    async def get_download_urls(
        self,
        metadata: VideoMetadata,
        quality: Optional[str] = None,
        cookies: Optional[Dict[str, str]] = None
    ) -> List[str]:
        """
        Get download URLs for video.
        
        Args:
            metadata: Video metadata
            quality: Desired quality (ignored for TikTok)
            cookies: Optional cookies
            
        Returns:
            List of download URLs
        """
        logger.info(f"Getting download URLs for: {metadata.video_id}")
        
        # Get video URL from metadata
        video_url = metadata.extra_data.get('video_url')
        if not video_url:
            raise PlatformError("No video URL found in metadata")
        
        return [video_url]
    
    def _extract_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from URL."""
        # Try full URL pattern
        match = re.search(r'/video/(\d+)', url)
        if match:
            return match.group(1)
        
        # Try short URL pattern (ID will be resolved later)
        for pattern in [r'vm\.tiktok\.com/(\w+)', r'vt\.tiktok\.com/(\w+)', r'tiktok\.com/t/(\w+)']:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    async def _resolve_short_url(self, short_url: str) -> str:
        """Resolve TikTok short URL to full URL."""
        logger.debug(f"Resolving short URL: {short_url}")
        
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(short_url)
            return str(response.url)
    
    async def _fetch_video_detail(
        self,
        video_id: str,
        cookies: Optional[Dict[str, str]]
    ) -> Dict:
        """
        Fetch video detail from TikTok.
        
        Note: This is a simplified implementation.
        Real implementation would need browser automation and A-Bogus signature.
        """
        logger.debug(f"Fetching video detail for: {video_id}")
        
        # Prepare headers (simplified)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.tiktok.com/',
        }
        
        # Construct video URL
        video_url = f'https://www.tiktok.com/@placeholder/video/{video_id}'
        
        # Make request
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    video_url,
                    headers=headers,
                    cookies=cookies or {},
                    timeout=10.0
                )
                response.raise_for_status()
                
                # Extract JSON data from HTML
                html = response.text
                video_data = self._extract_json_from_html(html)
                
                if not video_data:
                    raise VideoUnavailableError(f"Video not found: {video_id}")
                
                return video_data
                
        except httpx.HTTPError as e:
            logger.warning(f"HTTP error fetching video detail: {e}")
            raise PlatformError(f"Failed to fetch video detail: {e}")
    
    def _extract_json_from_html(self, html: str) -> Optional[Dict]:
        """Extract video JSON data from HTML."""
        # Try to find SIGI_STATE or __UNIVERSAL_DATA_FOR_REHYDRATION__
        patterns = [
            r'<script id="SIGI_STATE"[^>]*>(.*?)</script>',
            r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(1))
                    return data
                except json.JSONDecodeError:
                    continue
        
        return None
    
    def _parse_video_data(self, video_data: Dict, video_id: str) -> VideoMetadata:
        """Parse video data into VideoMetadata."""
        # This is a simplified parser
        # Real implementation would need to navigate the complex TikTok data structure
        
        # Try to extract basic info
        title = 'TikTok Video'
        author = 'Unknown'
        description = ''
        duration = 0
        thumbnail = ''
        video_url = None
        
        # Try different data structures
        if 'ItemModule' in video_data:
            item_module = video_data['ItemModule']
            if video_id in item_module:
                item = item_module[video_id]
                description = item.get('desc', '')
                title = description or 'TikTok Video'
                
                # Get video info
                video_info = item.get('video', {})
                duration = video_info.get('duration', 0)
                
                # Get download URL
                download_addr = video_info.get('downloadAddr')
                if download_addr:
                    video_url = download_addr
                
                # Get thumbnail
                cover = video_info.get('cover')
                if cover:
                    thumbnail = cover
                
                # Get author
                author_id = item.get('author')
                if author_id and 'UserModule' in video_data:
                    user_module = video_data['UserModule']
                    if author_id in user_module:
                        author = user_module[author_id].get('nickname', 'Unknown')
        
        # Create metadata
        metadata = VideoMetadata(
            platform=self.PLATFORM_NAME,
            video_id=video_id,
            title=title,
            author=author,
            description=description,
            duration=duration,
            thumbnail_url=thumbnail,
            available_qualities=[],  # TikTok doesn't provide quality options
            extra_data={
                'video_url': video_url,
            }
        )
        
        return metadata

    def get_platform_name(self) -> str:
        """Get platform name."""
        return self.PLATFORM_NAME
