"""
配置文件管理模块

支持多用户配置，随机选择用户进行登录。
"""
import os
import random
import shutil
from typing import Optional, List, Dict, Any
import toml
from .utils import get_local_ip


# 自动IP的标记值
AUTO_IP_MARKERS = {"auto", "自动", "<auto>", "*"}

# 配置文件名
CONFIG_FILE = "config.toml"
CONFIG_EXAMPLE_FILE = "config.example.toml"


class ConfigError(Exception):
    """配置文件错误异常"""
    pass


class UserConfig:
    """用户配置"""

    def __init__(self, username: str, password: str, ip: str, channel: str):
        self.username = username
        self.password = password
        self._ip = ip
        self.channel = channel

    @property
    def ip(self) -> str:
        """获取配置的原始IP值"""
        return self._ip

    def get_effective_ip(self) -> str:
        """
        获取有效的IP地址。
        如果IP为自动标记，则返回本机IP。
        """
        if self._ip.lower() in AUTO_IP_MARKERS:
            return get_local_ip()
        return self._ip

    def is_auto_ip(self) -> bool:
        """判断是否使用自动IP"""
        return self._ip.lower() in AUTO_IP_MARKERS

    def __repr__(self):
        return f"UserConfig(username={self.username!r}, ip={self._ip!r}, channel={self.channel!r})"


class AppConfig:
    """应用配置"""

    def __init__(self, config_path: str):
        """
        从配置文件加载配置。

        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self._config: Dict[str, Any] = {}
        self._users: List[UserConfig] = []

        self._load()

    def _load(self):
        """加载配置文件"""
        if not os.path.exists(self.config_path):
            raise ConfigError(f"配置文件不存在: {self.config_path}")

        try:
            self._config = toml.load(self.config_path)
        except Exception as e:
            raise ConfigError(f"配置文件解析失败: {e}") from e

        # 解析用户列表
        users_data = self._config.get("users", [])
        if not users_data:
            raise ConfigError("配置文件中没有定义用户 (users)")

        for user_data in users_data:
            try:
                user = UserConfig(
                    username=user_data["username"],
                    password=user_data["password"],
                    ip=user_data["ip"],
                    channel=user_data["channel"]
                )
                self._users.append(user)
            except KeyError as e:
                raise ConfigError(f"用户配置缺少必需字段: {e}") from e

    @property
    def users(self) -> List[UserConfig]:
        """获取所有用户配置"""
        return self._users

    @property
    def default_timeout(self) -> int:
        """获取默认超时时间"""
        return self._config.get("settings", {}).get("timeout", 10)

    def random_user(self) -> UserConfig:
        """随机选择一个用户"""
        return random.choice(self._users)

    def first_user(self) -> UserConfig:
        """获取第一个用户"""
        return self._users[0]


def init_config_file() -> bool:
    """
    初始化配置文件。

    如果 config.toml 不存在，从 config.example.toml 复制。

    Returns:
        True 如果配置文件已存在或成功创建，False 如果创建失败
    """
    config_path = os.path.join(os.getcwd(), CONFIG_FILE)
    example_path = os.path.join(os.getcwd(), CONFIG_EXAMPLE_FILE)

    # 配置文件已存在
    if os.path.exists(config_path):
        return True

    # 示例文件不存在，无法创建
    if not os.path.exists(example_path):
        return False

    # 从示例文件复制
    try:
        shutil.copy(example_path, config_path)
        return True
    except Exception:
        return False


def load_config(config_path: Optional[str] = None) -> Optional[AppConfig]:
    """
    加载配置文件。

    Args:
        config_path: 配置文件路径，如果为 None 则使用默认路径

    Returns:
        AppConfig 实例，如果配置文件不存在则返回 None
    """
    if config_path is None:
        config_path = os.path.join(os.getcwd(), CONFIG_FILE)

    if not os.path.exists(config_path):
        return None

    return AppConfig(config_path)
