from abc import ABC, abstractmethod
from typing import Any, List, Optional
import re
from django.conf import settings

class BaseFilter(ABC):
    @abstractmethod
    def filter(self, content: Any) -> Any:
        """过滤内容"""
        pass

class ContentFilter(BaseFilter):
    def __init__(self, sensitive_words: Optional[List[str]] = None):
        self.sensitive_words = sensitive_words or getattr(
            settings, 
            'SENSITIVE_WORDS', 
            ['spam', 'ad', '广告', '测试']
        )
        # 编译正则表达式以提高性能
        self.patterns = [
            re.compile(word, re.IGNORECASE) 
            for word in self.sensitive_words
        ]

    def filter(self, content: str) -> str:
        """过滤敏感内容"""
        if not content:
            return content

        filtered = content
        for pattern in self.patterns:
            filtered = pattern.sub(
                lambda m: '*' * len(m.group()), 
                filtered
            )

        return filtered
