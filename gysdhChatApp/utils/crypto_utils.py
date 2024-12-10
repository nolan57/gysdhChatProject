from cryptography.fernet import Fernet
from django.conf import settings
import base64
from django.core.exceptions import ImproperlyConfigured


class CryptoUtils:
    """
    提供加密和解密功能的工具类。
    
    使用Fernet对称加密算法实现数据的加密和解密。该类需要在Django settings中配置ENCRYPTION_KEY。
    
    Attributes:
        _fernet (Fernet): Fernet实例，用于加密解密操作的单例对象。
        
    Example:
        >>> # 在settings.py中设置
        >>> ENCRYPTION_KEY = 'your-32-byte-key'
        >>> 
        >>> # 使用示例
        >>> encrypted = CryptoUtils.encrypt("sensitive data")
        >>> decrypted = CryptoUtils.decrypt(encrypted)
    """
    _fernet = None

    @classmethod
    def _get_fernet(cls):
        """
        获取或创建Fernet实例。
        
        Returns:
            Fernet: 用于加密解密的Fernet实例
            
        Raises:
            ImproperlyConfigured: 如果settings中未设置ENCRYPTION_KEY
        """
        if cls._fernet is None:
            if not hasattr(settings, 'ENCRYPTION_KEY'):
                raise ImproperlyConfigured('ENCRYPTION_KEY must be set in settings')
            
            # 确保密钥是32位的URL安全的base64编码
            key = settings.ENCRYPTION_KEY
            if not isinstance(key, bytes):
                key = key.encode()
            
            # 如果密钥不是32位，进行填充或截断
            key = base64.urlsafe_b64encode(key.ljust(32)[:32])
            cls._fernet = Fernet(key)
        return cls._fernet

    @classmethod
    def encrypt(cls, text):
        """
        加密文本数据。
        
        Args:
            text (str or bytes): 需要加密的文本数据
            
        Returns:
            str: 加密后的文本。如果输入为空，返回空字符串
            
        Example:
            >>> encrypted = CryptoUtils.encrypt("sensitive data")
        """
        if not text:
            return ''
        if isinstance(text, str):
            text = text.encode()
        return cls._get_fernet().encrypt(text).decode()

    @classmethod
    def decrypt(cls, encrypted_text):
        """
        解密已加密的文本数据。
        
        Args:
            encrypted_text (str or bytes): 已加密的文本数据
            
        Returns:
            str: 解密后的原文。如果输入为空或解密失败，返回空字符串
            
        Example:
            >>> decrypted = CryptoUtils.decrypt(encrypted_text)
        """
        if not encrypted_text:
            return ''
        if isinstance(encrypted_text, str):
            encrypted_text = encrypted_text.encode()
        try:
            return cls._get_fernet().decrypt(encrypted_text).decode()
        except Exception:
            return ''  # 如果解密失败，返回空字符串
