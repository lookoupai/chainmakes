"""
API密钥加密工具模块
"""
from cryptography.fernet import Fernet
from app.config import settings


class KeyEncryption:
    """API密钥加密工具类"""
    
    def __init__(self):
        """初始化加密器"""
        # 从配置获取加密密钥
        self.key = settings.ENCRYPTION_KEY.encode()
        self.cipher = Fernet(self.key)
    
    def encrypt(self, api_key: str) -> str:
        """
        加密API密钥
        
        Args:
            api_key: 原始API密钥
            
        Returns:
            加密后的密钥字符串
        """
        if not api_key:
            return ""
        return self.cipher.encrypt(api_key.encode()).decode()
    
    def decrypt(self, encrypted_key: str) -> str:
        """
        解密API密钥
        
        Args:
            encrypted_key: 加密的API密钥
            
        Returns:
            解密后的原始密钥
        """
        if not encrypted_key:
            return ""
        return self.cipher.decrypt(encrypted_key.encode()).decode()


# 创建全局加密实例
key_encryption = KeyEncryption()

# 导出便捷函数
def encrypt_key(api_key: str) -> str:
    """加密API密钥的便捷函数"""
    return key_encryption.encrypt(api_key)

def decrypt_key(encrypted_key: str) -> str:
    """解密API密钥的便捷函数"""
    return key_encryption.decrypt(encrypted_key)