"""
生成加密密钥脚本
用于生成SECRET_KEY和ENCRYPTION_KEY
"""
import secrets
from cryptography.fernet import Fernet


def generate_secret_key(length: int = 32) -> str:
    """生成JWT SECRET_KEY"""
    return secrets.token_urlsafe(length)


def generate_encryption_key() -> str:
    """生成Fernet加密密钥"""
    return Fernet.generate_key().decode()


def main():
    print("=" * 60)
    print("生成安全密钥")
    print("=" * 60)
    print()
    
    # 生成JWT密钥
    secret_key = generate_secret_key()
    print("SECRET_KEY (用于JWT令牌):")
    print(f"  {secret_key}")
    print()
    
    # 生成加密密钥
    encryption_key = generate_encryption_key()
    print("ENCRYPTION_KEY (用于API密钥加密):")
    print(f"  {encryption_key}")
    print()
    
    print("=" * 60)
    print("请将以上密钥复制到 .env 文件中")
    print("⚠️  警告: 请妥善保管这些密钥,泄露可能导致安全问题")
    print("=" * 60)


if __name__ == "__main__":
    main()