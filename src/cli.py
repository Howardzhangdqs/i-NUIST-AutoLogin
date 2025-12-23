"""
校园网自动登录工具 - CLI 入口

提供命令行界面进行校园网登录。
支持配置文件多用户模式，随机选择用户登录。
"""
import sys
import argparse
import os
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt
from .client import LoginClient, LoginError
from .crypto import CHANNEL_MAP
from .config import load_config, AppConfig, ConfigError, UserConfig
from .utils import get_local_ip

# 创建全局 Console 实例
console = Console()


def print_banner():
    """打印程序标题"""
    console.log("\n[bold cyan]校园网自动登录工具[/bold cyan] [dim white]v1.0[/dim white]\n")


def print_channel_options():
    """打印网络出口选项"""
    console.log("[bright_black]网络出口选项:[/bright_black]")
    for cid, name in CHANNEL_MAP.items():
        console.log(f"  [cyan]{cid}[/cyan]: {name}")


def do_login(username: str, password: str, ip: str, channel: str, timeout: int = 10) -> int:
    """
    执行登录操作。

    Args:
        username: 用户名
        password: 密码
        ip: IP地址
        channel: 出口ID
        timeout: 超时时间

    Returns:
        退出码 (0=成功, 1=失败)
    """
    if channel not in CHANNEL_MAP:
        console.log(f"[red]错误: 无效的出口ID '{channel}'[/red]")
        console.log(f"有效选项: {', '.join(CHANNEL_MAP.keys())}")
        return 1

    channel_name = CHANNEL_MAP[channel]
    console.log(f"[dim]用户名:[/dim] {username}")
    console.log(f"[dim]IP地址:[/dim] {ip}")
    console.log(f"[dim]网络出口:[/dim] {channel_name}")

    client = LoginClient(timeout=timeout)

    # 使用进度条显示登录过程
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task(f"正在登录 [cyan]{channel_name}[/cyan]...", total=None)
        try:
            result = client.login(username, password, ip, channel)
            progress.remove_task(task)

            # 检查返回结果
            if result.get("code") == 200:
                user_data = result.get("data", {})
                console.log("[green]登录成功[/green]")
                console.log(f"[dim]  用户名:[/dim] {user_data.get('username', '-')}")
                console.log(f"[dim]  IP地址:[/dim] {user_data.get('usripadd', '-')}")
                console.log(f"[dim]  网络出口:[/dim] {user_data.get('outport', '-')}")
                console.log(f"[dim]  余额:[/dim] [yellow]{user_data.get('balance', '0.00')}[/yellow]")
                console.log(f"[dim]  在线时长:[/dim] [blue]{user_data.get('duration', '0')} 秒[/blue]")
                return 0
            else:
                console.log(f"[red]登录失败: {result.get('message', '未知错误')}[/red]")
                return 1

        except LoginError as e:
            progress.remove_task(task)
            console.log(f"[red]登录失败: {e}[/red]")
            return 1


def interactive_mode():
    """交互式登录模式"""
    print_banner()

    username = Prompt.ask("[cyan]用户名[/cyan]")
    password = Prompt.ask("[cyan]密码[/cyan]", password=True)
    ip_address = Prompt.ask("[cyan]IP地址[/cyan]")

    print_channel_options()

    choices = list(CHANNEL_MAP.keys())
    choice_str = "/".join(choices)

    while True:
        selected_channel_id = Prompt.ask(
            f"[cyan]出口ID[/cyan] ({choice_str})",
            choices=choices,
        )
        if selected_channel_id in CHANNEL_MAP:
            break

    return do_login(username, password, ip_address, selected_channel_id)


def config_mode(config: AppConfig, random: bool = False, timeout: int = None) -> int:
    """
    配置文件模式。

    Args:
        config: 配置对象
        random: 是否随机选择用户
        timeout: 超时时间（如果为 None 则使用配置文件中的值）

    Returns:
        退出码
    """
    # 选择用户
    if random:
        user = config.random_user()
        console.log(f"[dim]配置模式: 从 {len(config.users)} 个用户中随机选择[/dim]")
    else:
        user = config.first_user()
        console.log(f"[dim]配置模式: 使用第一个用户[/dim]")

    # 超时时间
    if timeout is None:
        timeout = config.default_timeout

    effective_ip = user.get_effective_ip()
    is_auto_ip = user.is_auto_ip()
    channel_name = CHANNEL_MAP.get(user.channel, user.channel)

    if is_auto_ip:
        console.log(f"[dim]用户名:[/dim] {user.username}")
        console.log(f"[dim]IP地址:[/dim] [yellow]auto -> {effective_ip}[/yellow]")
        console.log(f"[dim]网络出口:[/dim] {channel_name}")
    else:
        console.log(f"[dim]用户名:[/dim] {user.username}")
        console.log(f"[dim]IP地址:[/dim] {effective_ip}")
        console.log(f"[dim]网络出口:[/dim] {channel_name}")

    client = LoginClient(timeout=timeout)

    # 使用进度条显示登录过程
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task(f"正在登录 [cyan]{channel_name}[/cyan]...", total=None)
        try:
            result = client.login(user.username, user.password, effective_ip, user.channel)
            progress.remove_task(task)

            # 检查返回结果
            if result.get("code") == 200:
                user_data = result.get("data", {})
                console.log("[green]登录成功[/green]")
                console.log(f"[dim]  用户名:[/dim] {user_data.get('username', '-')}")
                console.log(f"[dim]  IP地址:[/dim] {user_data.get('usripadd', '-')}")
                console.log(f"[dim]  网络出口:[/dim] {user_data.get('outport', '-')}")
                console.log(f"[dim]  余额:[/dim] [yellow]{user_data.get('balance', '0.00')}[/yellow]")
                console.log(f"[dim]  在线时长:[/dim] [blue]{user_data.get('duration', '0')} 秒[/blue]")
                return 0
            else:
                console.log(f"[red]登录失败: {result.get('message', '未知错误')}[/red]")
                return 1

        except LoginError as e:
            progress.remove_task(task)
            console.log(f"[red]登录失败: {e}[/red]")
            return 1


def main():
    """主入口函数"""
    parser = argparse.ArgumentParser(
        description="校园网自动登录工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
[示例]
  %(prog)s                        # 交互式模式
  %(prog)s -u user -p pass --auto-ip -c 3   # 命令行模式（自动IP）
  %(prog)s -u user -p pass -i 1.2.3.4 -c 3   # 命令行模式（指定IP）
  %(prog)s -C config.toml         # 使用配置文件（第一个用户）
  %(prog)s -C config.toml -r      # 使用配置文件（随机用户）
  %(prog)s -C config.toml -r --timeout 5   # 指定超时时间

[优先级] 命令行参数 > 配置文件 > 交互式输入

配置文件中 ip 设为 "auto" 可自动获取本机IP。
        """
    )
    parser.add_argument(
        "-u", "--username",
        help="用户名"
    )
    parser.add_argument(
        "-p", "--password",
        help="密码"
    )
    parser.add_argument(
        "-i", "--ip",
        help="IP地址"
    )
    parser.add_argument(
        "--auto-ip",
        action="store_true",
        help="自动获取本机IP地址"
    )
    parser.add_argument(
        "-c", "--channel",
        choices=list(CHANNEL_MAP.keys()),
        help="网络出口 (1=校园网, 2=中国移动, 3=中国电信, 4=中国联通)"
    )
    parser.add_argument(
        "-C", "--config",
        default="config.toml",
        help="配置文件路径 (TOML格式)"
    )
    parser.add_argument(
        "-r", "--random",
        action="store_true",
        help="从配置文件中随机选择用户（需配合 -C 使用）"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        help="请求超时时间（秒），默认10或配置文件中的值"
    )

    args = parser.parse_args()

    # 模式 1: 命令行参数完整模式（优先级最高）
    if args.username and args.password and args.channel:
        timeout = args.timeout or 10
        # 处理IP
        if args.auto_ip:
            ip = get_local_ip()
            console.log(f"[dim]自动获取IP: {ip}[/dim]\n")
        else:
            ip = args.ip
            if not ip:
                console.log("[red]请使用 -i 指定IP地址或使用 --auto-ip 自动获取[/red]")
                return 1
        return do_login(args.username, args.password, ip, args.channel, timeout)

    # 模式 2: 配置文件模式
    config_path = args.config or os.path.join(os.getcwd(), "config.toml")

    try:
        config = load_config(config_path)
        if config:
            return config_mode(config, random=args.random, timeout=args.timeout)
    except ConfigError as e:
        console.log(f"[red]配置错误: {e}[/red]")
        return 1

    # 如果指定了配置文件但不存在
    if args.config:
        console.log(f"[red]配置文件不存在: {args.config}[/red]")
        return 1

    # 模式 3: 交互式模式
    return interactive_mode()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        console.log("\n[yellow]已取消[/yellow]")
        sys.exit(130)
