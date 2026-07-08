# Vincent

`Vincent` 是一个用于整理和发布可复用本地 `MCP plugin` 的仓库。当前主产物是 `fastaicode-image-mcp`，它把 FastAICode 兼容图片接口封装成两个可直接被 MCP host 调用的工具：

- `generate_image`：文生图并自动保存本地 `PNG`
- `edit_image`：基于本地图片做图生图编辑并自动保存本地 `PNG`

## 当前仓库结构

```text
.
├── CURRENT_TASK.md
├── DECISIONS.md
├── docs/
│   ├── plans/
│   └── requirements/
├── fastaicode-image-mcp/
│   ├── .codex-plugin/
│   ├── .mcp.json
│   ├── README.md
│   ├── examples/
│   ├── server/
│   ├── skills/
│   └── tests/
└── outputs/
    └── runtime/
        └── vibe-sessions/
```

## MCP 结构怎么用

当前插件目录 `fastaicode-image-mcp/` 里有四层关键结构：

1. `.codex-plugin/plugin.json`
   - 插件元数据入口
   - 声明插件名称、Skill 目录和 MCP server 配置文件位置

2. `.mcp.json`
   - MCP host 读取的本地 server 注册文件
   - 当前默认使用 `python3 ./fastaicode-image-mcp/server/mcp_server.py`

3. `server/`
   - `mcp_server.py`：MCP / JSON-RPC 入口，处理 `initialize`、`ping`、`tools/list`、`tools/call`
   - `client.py`：向 FastAICode 图片接口发请求并解析响应
   - `config.py`：读取 `fastaicode-image-mcp.toml` 与环境变量
   - `naming.py`：输出文件命名
   - `models.py`：响应数据模型

4. `skills/fastaicode-image/SKILL.md`
   - 说明什么时候调用 `generate_image`
   - 说明什么时候调用 `edit_image`
   - 约束 `1k / 2k / 4k / auto` 的使用语义

## 快速开始

```bash
git clone git@github.com:Innnoa/MCP_Vincent.git
cd Vincent/fastaicode-image-mcp
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install httpx pytest
cp .env.example .env
set -a
source .env
set +a
pytest tests -v
```

默认配置文件是 `fastaicode-image-mcp/fastaicode-image-mcp.toml`。如果你要改接口地址、默认模型或默认输出目录，直接修改这个文件即可。

## 示例

| 文生图 (`generate_image`) | 文生图 (`generate_image`) |
|:---:|:---:|
| ![fox logo](docs/screenshots/example-fox-logo.png) | ![rubber duck](docs/screenshots/example-rubber-duck.png) |
| *orange fox logo* | *cute rubber duck* |

更多参数说明见 `fastaicode-image-mcp/README.md`。

## 部署方式

当前仓库推荐“源码部署”：

1. 保留 `fastaicode-image-mcp/` 目录结构不变
2. 安装 Python 依赖
3. 设置 `FASTAICODE_API_KEY`
4. 让 MCP host 指向 `fastaicode-image-mcp/.mcp.json`

如果你的 MCP host 会以当前仓库根目录作为工作目录启动 server，当前 `.mcp.json` 可以直接使用。

如果你的 MCP host 不会以当前仓库根目录作为工作目录启动，请把 `fastaicode-image-mcp/.mcp.json` 里的 `./fastaicode-image-mcp/server/mcp_server.py` 改成你本机上的绝对路径；这类本地路径差异建议只在本机改，不要直接提交回 GitHub。

更完整的工具参数、目录说明和调用示例见 `fastaicode-image-mcp/README.md`。

## 本地验证

```bash
pytest fastaicode-image-mcp/tests -v
```

## 当前限制

- 默认只支持本地文件输入的图生图编辑
- 没有实现多图输入、URL 输入和 mask
- `4k` 是否可用取决于 `fastaicode-image-mcp.toml` 里的映射
