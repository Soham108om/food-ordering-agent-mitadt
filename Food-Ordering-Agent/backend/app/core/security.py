from cryptography.fernet import Fernet
from app.core.config import settings

def encrypt_token(plain_token: str) -> str:
    """
    Encrypts sensitive tokens (e.g. Swiggy Access Token) before persisting to storage.
    """
    if not plain_token:
        return ""
    f = Fernet(settings.get_fernet_key())
    return f.encrypt(plain_token.encode("utf-8")).decode("utf-8")

def decrypt_token(encrypted_token: str) -> str:
    """
    Decrypts sensitive tokens retrieved from persistent storage.
    """
    if not encrypted_token:
        return ""
    try:
        f = Fernet(settings.get_fernet_key())
        return f.decrypt(encrypted_token.encode("utf-8")).decode("utf-8")
    except Exception as e:
        raise ValueError(f"Failed to decrypt Swiggy access token: {str(e)}")
