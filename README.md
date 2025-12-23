# 校园网自动登录工具

基于学长智慧的 Python 校园网自动登录工具，支持多种网络出口和多用户配置。适用于 **2025年8月** 之后的校园网登录系统。

## 功能特性

- 支持 AES/ECB/PKCS7 加密
- 支持四种网络出口：校园网、中国移动、中国电信、中国联通
- 提供交互式、命令行参数、配置文件三种使用模式
- 支持多用户配置，可随机选择用户登录

## 安装

```bash
# 创建虚拟环境
uv venv

# 激活虚拟环境
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 安装依赖
uv sync

# 复制配置文件
cp config.example.toml config.toml
```

## 使用方法

### 方式一：交互式模式

```bash
uv run python -m src.cli
```

按提示输入用户名、密码、IP地址和选择网络出口。

### 方式二：命令行参数模式

```bash
uv run python -m src.cli -u <用户名> -p <密码> -i <IP地址> -c <出口ID>
```

**参数说明：**

| 参数 | 说明 |
|------|------|
| `-u, --username` | 用户名 |
| `-p, --password` | 密码 |
| `-i, --ip` | IP地址 |
| `-c, --channel` | 网络出口ID |
| `--timeout` | 请求超时时间（秒），默认10 |
| `-C, --config` | 配置文件路径 |
| `-r, --random` | 随机选择用户（需配合 -C 使用） |

**网络出口ID：**

| ID | 出口 |
|----|------|
| 1 | 校园网 |
| 2 | 中国移动 |
| 3 | 中国电信 |
| 4 | 中国联通 |

### 方式三：配置文件模式（推荐）

在项目根目录创建 `config.toml`：

```toml
# 全局设置
[settings]
timeout = 10

# 用户列表
[[users]]
username = "your_username"
password = "your_password"
ip = "auto"      # 自动获取本机IP地址
channel = "3"    # 1=校园网, 2=移动, 3=电信, 4=联通

[[users]]
username = "another_username"
password = "another_password"
ip = "10.255.255.101"  # 指定IP地址
channel = "2"
```

**使用配置文件：**

```bash
# 使用第一个用户
uv run python -m src.cli -C config.toml

# 随机选择用户
uv run python -m src.cli -C config.toml -r

# 指定超时时间
uv run python -m src.cli -C config.toml -r --timeout 5

# 使用自定义配置文件路径
uv run python -m src.cli -C /path/to/custom-config.toml
```

### 优先级

**命令行参数 > 配置文件 > 交互式输入**

当提供完整的命令行参数（`-u -p -i -c`）时，会强制使用命令行参数，忽略配置文件。

### 示例

```bash
# 交互式模式
uv run python -m src.cli

# 命令行模式
uv run python -m src.cli -u myuser -p mypass -i 10.255.255.100 -c 3

# 配置文件模式（第一个用户）
uv run python -m src.cli -C config.toml

# 配置文件模式（随机用户）
uv run python -m src.cli -C config.toml -r
```

## 项目结构

```
autologin/
├── src/
│   ├── __init__.py    # 包初始化
│   ├── crypto.py      # AES 加密模块
│   ├── client.py      # HTTP 登录客户端
│   ├── config.py      # 配置文件管理
│   └── cli.py         # CLI 命令行入口
├── config.toml        # 配置文件示例
├── pyproject.toml     # 项目配置
└── README.md
```

## 技术栈

- **Python**: 3.12+
- **包管理**: uv
- **加密库**: pycryptodome
- **HTTP库**: httpx
- **配置解析**: toml
