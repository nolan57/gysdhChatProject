from cryptography.fernet import Fernet
from django.conf import settings
import json
import base64

class EncryptionService:
    def __init__(self):
        # 从settings获取密钥，如果没有则生成新密钥
        key = getattr(settings, 'ENCRYPTION_KEY', None)
        if not key:
            key = Fernet.generate_key()
        elif isinstance(key, str):
            # 如果密钥是字符串，确保它是正确的base64编码
            try:
                # 尝试解码并重新编码以确保格式正确
                key = base64.urlsafe_b64encode(base64.urlsafe_b64decode(key.encode()))
            except:
                # 如果解码失败，生成新密钥
                key = Fernet.generate_key()
        
        self.fernet = Fernet(key)
    
    def encrypt(self, data):
        """
        加密数据
        :param data: 要加密的数据（可以是任何可JSON序列化的数据）
        :return: 加密后的字符串
        """
        try:
            # 将数据转换为JSON字符串
            json_data = json.dumps(data)
            # 加密
            encrypted_data = self.fernet.encrypt(json_data.encode())
            # 转换为base64字符串
            return base64.b64encode(encrypted_data).decode()
        except Exception as e:
            print(f"加密失败: {str(e)}")
            return None

    def decrypt(self, encrypted_data):
        """
        解密数据
        :param encrypted_data: 加密的字符串
        :return: 解密后的数据
        """
        try:
            # 从base64字符串转换回bytes
            encrypted_bytes = base64.b64decode(encrypted_data.encode())
            # 解密
            decrypted_data = self.fernet.decrypt(encrypted_bytes)
            # 解析JSON
            return json.loads(decrypted_data.decode())
        except Exception as e:
            print(f"解密失败: {str(e)}")
            return None

# 创建单例实例
encryption_service = EncryptionService()
