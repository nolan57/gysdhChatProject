from PIL import Image
import bleach
import magic
import os
from django.conf import settings
from django.utils.html import escape
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class SecurityService:
    ALLOWED_TAGS = [
        # 基本格式
        'p', 'br', 'hr',
        # 文本格式化
        'strong', 'b', 'em', 'i', 'u', 's', 'strike', 'del', 'sub', 'sup',
        # 标题
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        # 列表
        'ul', 'ol', 'li',
        # 链接和图片
        'a', 'img',
        # 表格
        'table', 'thead', 'tbody', 'tfoot', 'tr', 'td', 'th', 'col', 'colgroup',
        # 容器
        'div', 'span',
        # 其他
        'blockquote', 'pre', 'code'
    ]

    ALLOWED_ATTRIBUTES = {
        # 全局属性
        '*': ['class', 'style', 'id', 'align', 'data-*', 'data-darkreader-inline-color'],
        # 链接和图片
        'a': ['href', 'target', 'rel', 'title'],
        'img': ['src', 'alt', 'title', 'width', 'height'],
        # 表格相关
        'table': ['border', 'cellpadding', 'cellspacing', 'width', 'style', 'align'],
        'colgroup': ['span', 'width', 'style'],
        'col': ['span', 'width', 'style'],
        'th': ['colspan', 'rowspan', 'width', 'style', 'align', 'valign', 'scope'],
        'td': ['colspan', 'rowspan', 'width', 'style', 'align', 'valign'],
        # 列表相关
        'ol': ['type', 'start', 'style'],
        'ul': ['type', 'style'],
        'li': ['value', 'type', 'style'],
        # 其他元素
        'p': ['style', 'align'],
        'div': ['style', 'align'],
        'span': ['style'],
        'pre': ['style'],
        'code': ['style'],
        'blockquote': ['style'],
    }

    ALLOWED_STYLES = [
        # 文本样式
        'font-family', 'font-size', 'font-weight', 'font-style',
        'text-decoration', 'text-align', 'line-height',
        'letter-spacing', 'text-transform', 'white-space',
        # 颜色
        'color', 'background-color',
        # 边距和填充
        'margin', 'margin-top', 'margin-right', 'margin-bottom', 'margin-left',
        'padding', 'padding-top', 'padding-right', 'padding-bottom', 'padding-left',
        # 边框
        'border', 'border-width', 'border-style', 'border-color',
        'border-top', 'border-right', 'border-bottom', 'border-left',
        'border-collapse',
        # 尺寸
        'width', 'height', 'min-width', 'max-width',
        # 列表样式
        'list-style', 'list-style-type',
        # 其他
        'display', 'float', 'clear', 'vertical-align'
    ]

    ALLOWED_IMAGE_TYPES = {
        'image/jpeg': '.jpg',
        'image/png': '.png',
        'image/gif': '.gif',
        'image/webp': '.webp'
    }

    MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB

    @classmethod
    def sanitize_html(cls, content):
        """
        清理和验证HTML内容
        """
        if not content:
            return content

        try:
            # 移除多余的空白字符
            content = content.strip()
            
            # 使用bleach进行HTML清理
            cleaned_content = bleach.clean(
                content,
                tags=cls.ALLOWED_TAGS,
                attributes=cls.ALLOWED_ATTRIBUTES,
                strip=True,
                strip_comments=True,
                protocols=['http', 'https', 'mailto', 'tel']
            )
            
            return cleaned_content
            
        except Exception as e:
            logger.error(f"HTML sanitization error: {str(e)}")
            return escape(content)

    @classmethod
    def validate_image(cls, file) -> Tuple[bool, Optional[str]]:
        """
        验证上传的图片文件
        返回: (是否有效, 错误信息)
        """
        try:
            # 检查文件大小
            if file.size > cls.MAX_IMAGE_SIZE:
                return False, f"文件大小超过限制（最大{cls.MAX_IMAGE_SIZE/1024/1024}MB）"

            # 使用python-magic检查文件类型
            file_type = magic.from_buffer(file.read(1024), mime=True)
            file.seek(0)  # 重置文件指针

            if file_type not in cls.ALLOWED_IMAGE_TYPES:
                return False, "不支持的文件类型"

            # 使用PIL验证图片完整性
            try:
                with Image.open(file) as img:
                    img.verify()
                file.seek(0)  # verify会消耗文件对象，需要重置
                
                # 再次打开检查格式
                with Image.open(file) as img:
                    if img.format.lower() not in [fmt.replace('image/', '') for fmt in cls.ALLOWED_IMAGE_TYPES]:
                        return False, "图片格式验证失败"
                    
                    # 检查图片尺寸
                    if max(img.size) > 4096:  # 最大4096像素
                        return False, "图片尺寸过大"

                file.seek(0)  # 再次重置文件指针
            except Exception as e:
                logger.error(f"Image validation error: {str(e)}")
                return False, "图片验证失败"

            return True, None

        except Exception as e:
            logger.error(f"File validation error: {str(e)}")
            return False, "文件验证失败"

    @classmethod
    def get_secure_filename(cls, original_filename: str, file_type: str) -> str:
        """
        生成安全的文件名
        """
        import uuid
        ext = cls.ALLOWED_IMAGE_TYPES.get(file_type, '.jpg')
        return f"{uuid.uuid4().hex}{ext}"

    @classmethod
    def clean_old_uploads(cls, days: int = 30) -> None:
        """
        清理指定天数前的上传文件
        """
        import time
        from datetime import datetime, timedelta
        
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads', 'images')
        if not os.path.exists(upload_dir):
            return

        threshold = datetime.now() - timedelta(days=days)
        
        for filename in os.listdir(upload_dir):
            filepath = os.path.join(upload_dir, filename)
            try:
                # 获取文件修改时间
                mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                if mtime < threshold:
                    # 检查文件是否仍在使用
                    if not cls.is_file_referenced(filename):
                        os.remove(filepath)
                        logger.info(f"Removed old upload: {filename}")
            except Exception as e:
                logger.error(f"Error cleaning old upload {filename}: {str(e)}")

    @classmethod
    def is_file_referenced(cls, filename: str) -> bool:
        """
        检查文件是否被引用在公告中
        """
        from ..models import Announcement
        return Announcement.objects.filter(content__contains=filename).exists()

    @classmethod
    def get_secure_headers(cls) -> dict:
        """
        获取安全的HTTP响应头
        """
        return {
            'Content-Security-Policy': "default-src 'self'; img-src 'self' data: blob:; style-src 'self' 'unsafe-inline';",
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'SAMEORIGIN',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()'
        }
