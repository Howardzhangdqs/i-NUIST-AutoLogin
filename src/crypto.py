"""
校园网登录加密模块

提供 AES/ECB/PKCS7 加密功能，用于构建登录请求 payload。
"""
import hashlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import binascii


# --- 常量定义 ---

STATIC_KEY_AND_SALT = "axaQiQpsdFAacccs"

CHANNEL_MAP = {
    "1": "校园网",
    "3": "中国电信",
    "2": "中国移动",
    "4": "中国联通"
}


# --- 加密函数 ---

def generate_dynamic_key(username: str) -> bytes:
    """
    根据用户名生成16字节的动态AES密钥 (用于除username外的所有字段)。

    Args:
        username: 用户名

    Returns:
        16字节的AES密钥
    """
    pre_key = STATIC_KEY_AND_SALT + username
    hashed_key = hashlib.sha256(pre_key.encode('utf-8')).hexdigest()
    return hashed_key[:16].encode('utf-8')


def encrypt_data(data: str, key: bytes) -> str:
    """
    使用AES/ECB/PKCS7对数据进行加密。

    Args:
        data: 待加密的明文字符串
        key: AES密钥 (16字节)

    Returns:
        十六进制格式的加密字符串
    """
    data_bytes = data.encode('utf-8')
    cipher = AES.new(key, AES.MODE_ECB)
    padded_data = pad(data_bytes, AES.block_size)
    encrypted_data = cipher.encrypt(padded_data)
    return binascii.hexlify(encrypted_data).decode('utf-8')


def build_login_payload(
    username: str,
    password: str,
    ip_address: str,
    channel_id: str
) -> dict:
    """
    构建完全符合业务逻辑的、加密后的登录请求体。

    Args:
        username: 用户名
        password: 密码
        ip_address: IP地址
        channel_id: 出口ID (1=校园网, 2=中国移动, 3=中国电信, 4=中国联通)

    Returns:
        包含加密后字段的请求体字典
    """
    # 准备两个密钥
    static_key = STATIC_KEY_AND_SALT.encode('utf-8')
    dynamic_key = generate_dynamic_key(username)

    # 分别进行加密
    # 特殊处理：username 使用静态密钥
    encrypted_username = encrypt_data(username, static_key)

    # 其他字段使用动态密钥
    encrypted_password = encrypt_data(password, dynamic_key)
    encrypted_ifautologin = encrypt_data("1", dynamic_key)
    encrypted_channel = encrypt_data(channel_id, dynamic_key)
    encrypted_pagesign = encrypt_data("secondauth", dynamic_key)
    encrypted_usripadd = encrypt_data(ip_address, dynamic_key)

    # 组装 payload
    return {
        "username": encrypted_username,
        "password": encrypted_password,
        "ifautologin": encrypted_ifautologin,
        "channel": encrypted_channel,
        "pagesign": encrypted_pagesign,
        "usripadd": encrypted_usripadd,
    }
