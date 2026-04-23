# FastAICode Image MCP

本目录是一个可复用的本地 `MCP plugin`，把 FastAICode 兼容图片接口封装成两个工具：

- `generate_image`
- `edit_image`

工具会负责发请求、解析 `b64_json`、解码图片并把结果保存为本地 `PNG`。

## 目录结构

```text
fastaicode-image-mcp/
├── .codex-plugin/plugin.json
├── .mcp.json
├── .env.example
├── examples/
│   └── fastaicode-image.example.toml
├── server/
│   ├── client.py
│   ├── config.py
│   ├── mcp_server.py
│   ├── models.py
│   └── naming.py
├── skills/
│   └── fastaicode-image/SKILL.md
├── tests/
└── fastaicode-image-mcp.toml
```

## 这几个文件分别做什么

### `.codex-plugin/plugin.json`

- 声明插件元数据
- 告诉宿主去哪里找 Skill
- 告诉宿主去哪里找 `.mcp.json`

### `.mcp.json`

- 注册本地 MCP server
- 当前默认入口是 `python3 ./fastaicode-image-mcp/server/mcp_server.py`
- 当前配置默认假定宿主从仓库根目录启动
- 如果宿主不是从仓库根目录启动，可能需要把相对路径改成绝对路径

### `server/mcp_server.py`

- MCP / JSON-RPC 入口
- 支持 `initialize`
- 支持 `ping`
- 支持 `tools/list`
- 支持 `tools/call`
- 同时兼容“单行 JSON”与 `Content-Length` 两种输入方式

### `server/config.py`

- 读取 `fastaicode-image-mcp.toml`
- 读取并覆盖环境变量：
  - `FASTAICODE_API_KEY`
  - `FASTAICODE_BASE_URL`

### `server/client.py`

- 调用：
  - `POST /v1/images/generations`
  - `POST /v1/images/edits`
- 解析 `data[0].b64_json`
- 把响应交给落盘逻辑

### `skills/fastaicode-image/SKILL.md`

- 约束调用时机
- 约束 `1k / 2k / 4k / auto` 的语义
- 约束报错时该如何回传给用户

## 运行前准备

要求：

- Python `3.11+`
- 可访问的 FastAICode 兼容图片接口
- 环境变量 `FASTAICODE_API_KEY`

安装最小依赖：

```bash
cd fastaicode-image-mcp
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install httpx pytest
```

环境变量示例：

```bash
cp .env.example .env
set -a
source .env
set +a
```

默认配置文件是 `fastaicode-image-mcp.toml`。示例模板在 `examples/fastaicode-image.example.toml`。

## 部署方式

### 方式 1：源码目录直接部署

适合本地仓库直接接入 MCP host。

1. 安装依赖
2. 配置 `FASTAICODE_API_KEY`
3. 保持当前目录结构不变
4. 让宿主加载本目录的 `.mcp.json`
5. 确认宿主工作目录是仓库根目录

当前 `.mcp.json` 内容：

```json
{
  "mcpServers": {
    "fastaicode-image": {
      "command": "python3",
      "args": [
        "./fastaicode-image-mcp/server/mcp_server.py"
      ]
    }
  }
}
```

### 方式 2：改成本机绝对路径部署

如果你的宿主不是从 `fastaicode-image-mcp/` 目录启动，直接把 `.mcp.json` 改成绝对路径即可，例如：

```json
{
  "mcpServers": {
    "fastaicode-image": {
      "command": "python3",
      "args": [
        "/absolute/path/to/fastaicode-image-mcp/server/mcp_server.py"
      ]
    }
  }
}
```

这类路径改动只建议保留在本机，不建议直接提交回公共仓库。

## 工具参数

### `generate_image`

必填：

- `prompt`

可选：

- `size_preset`: `1k | 2k | 4k | auto`
- `output_path`
- `filename_hint`
- `model`

最小示例：

```json
{
  "prompt": "a minimal red circle icon on a clean white background",
  "size_preset": "1k"
}
```

### `edit_image`

必填：

- `prompt`
- `input_image_path`

可选：

- `size_preset`: `1k | 2k | 4k | auto`
- `output_path`
- `filename_hint`
- `model`

最小示例：

```json
{
  "prompt": "turn this into a flat blue icon",
  "input_image_path": "/absolute/path/to/source.png",
  "size_preset": "auto"
}
```

## 输出规则

- 默认输出目录来自 `fastaicode-image-mcp.toml`
- 当前默认相对路径是 `outputs/images`
- 因为配置文件位于插件根目录，所以当前实际默认落盘位置是 `fastaicode-image-mcp/outputs/images/`
- 如果显式传入 `output_path`，则优先使用该路径

## 本地验证

运行测试：

```bash
pytest tests -v
```

直接启动 server：

```bash
python3 server/mcp_server.py
```

在无输入时它会直接退出；被 MCP host 拉起时会从标准输入读取 JSON-RPC 请求。

## 已知限制

- 默认只支持本地 `png` 输入做图生图
- 没有实现多图输入、URL 输入和 mask
- `4k` 是否可用取决于 `fastaicode-image-mcp.toml` 的映射
