"""
工具函数模块
"""
import socket


def get_all_local_ips() -> list[str]:
    """
    获取本机所有网络接口的IP地址。

    Returns:
        所有IP地址列表
    """
    ips = set()
    hostname = socket.gethostname()

    # 方法1: 通过主机名获取
    try:
        addr_infos = socket.getaddrinfo(hostname, None)
        for addr in addr_infos:
            ip = addr[4][0]
            if ":" not in ip:  # 排除IPv6
                ips.add(ip)
    except Exception:
        pass

    # 方法2: 尝试获取所有网络接口
    try:
        # 获取本机所有IP地址
        for iface in socket.getaddrinfo(socket.gethostname(), None):
            ip = iface[4][0]
            if ":" not in ip:
                ips.add(ip)
    except Exception:
        pass

    # 方法3: 通过连接到不同网段推断
    test_targets = [
        "10.255.255.16",  # 校园网认证服务器
        "114.114.114.114",  # 公网DNS
        "8.8.8.8",          # Google DNS
    ]

    for target in test_targets:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.settimeout(0.1)
                s.connect((target, 80))
                ip = s.getsockname()[0]
                ips.add(ip)
        except Exception:
            pass

    return sorted(list(ips), key=lambda x: x.split("."))


def print_all_ips():
    """打印所有本机IP地址"""
    ips = get_all_local_ips()
    print("=" * 50)
    print("本机所有IP地址:")
    print("=" * 50)
    for i, ip in enumerate(ips, 1):
        print(f"  [{i}] {ip}")
    print("=" * 50)
    return ips


def get_local_ip() -> str:
    """
    获取本机局域网IP地址。

    优先获取与目标服务器同一网段的IP地址。

    Returns:
        本机IP地址，如果获取失败则返回 "127.0.0.1"
    """
    ips = get_all_local_ips()

    # 优先选择10.x.x.x网段的IP（校园网常见网段）
    for ip in ips:
        if ip.startswith("10.") and not ip.startswith("10.255."):
            return ip

    # 其次选择192.168.x.x网段
    for ip in ips:
        if ip.startswith("192.168."):
            return ip

    # 再次选择172.16-31.x.x网段
    for ip in ips:
        parts = ip.split(".")
        if len(parts) == 4 and parts[0] == "172" and 16 <= int(parts[1]) <= 31:
            return ip

    # 返回第一个非127.0.0.1的IP
    for ip in ips:
        if not ip.startswith("127."):
            return ip

    return "127.0.0.1"


if __name__ == "__main__":
    # 测试：打印所有IP
    print_all_ips()
    print(f"\n自动选择的IP: {get_local_ip()}")
