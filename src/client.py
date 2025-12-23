"""
校园网登录 HTTP 客户端

提供登录 API 调用功能。
"""
import httpx
from typing import Dict, Any
from .crypto import build_login_payload


# --- 常量定义 ---

LOGIN_URL = "http://10.255.255.16/api/v1/login"

REQUEST_HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
    "access-control-allow-origin": "*",
    "content-type": "application/json;charset=UTF-8"
}


# --- 异常类 ---

class LoginError(Exception):
    """登录失败异常"""
    pass


# --- 客户端类 ---

class LoginClient:
    """
    校园网登录客户端

    负责构建加密后的登录 payload 并发送到认证服务器。
    """

    def __init__(self, timeout: int = 10):
        """
        初始化客户端。

        Args:
            timeout: 请求超时时间（秒）
        """
        self.timeout = timeout

    def login(
        self,
        username: str,
        password: str,
        ip_address: str,
        channel_id: str
    ) -> Dict[str, Any]:
        """
        执行登录操作。

        Args:
            username: 用户名
            password: 密码
            ip_address: 客户端IP地址
            channel_id: 网络出口ID

        Returns:
            服务器响应的JSON数据

        Raises:
            LoginError: 登录失败时抛出
        """
        # 构建加密后的 payload
        payload = build_login_payload(username, password, ip_address, channel_id)

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    LOGIN_URL,
                    json=payload,
                    headers=REQUEST_HEADERS
                )
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:
            raise LoginError(f"HTTP错误: {e.response.status_code}") from e
        except httpx.RequestError as e:
            raise LoginError(f"网络请求失败: {e}") from e
        except Exception as e:
            raise LoginError(f"登录失败: {e}") from e
