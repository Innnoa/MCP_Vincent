# FastAICode Image MCP Plugin Requirements

日期：2026-04-23

## 1. 目标

在本地实现一个可复用的 MCP 插件，让 Codex 可以通过标准化工具调用 `http://new.fastaicode.top/v1/images/generations` 文生图接口。

首版交付包含两层：

- 本地 `MCP server`，提供可执行图片生成工具
- 配套 `Skill`，约束何时调用、如何传参、如何处理常见错误

## 2. 首版范围

当前版本实现两个可执行工具：

- `generate_image`
- `edit_image`

首版行为：

- 接收提示词并调用远端图片生成接口
- 支持基于本地输入图片进行图生图编辑
- 支持标准化尺寸档位：`1k`、`2k`、`4k`、`auto`
- 支持默认输出目录和显式输出路径
- 自动解析 `b64_json`
- 自动将图片保存为本地 `png`
- 返回结构化结果，供 Codex 和用户消费

## 3. 非目标

首版不包含以下能力：

- 图片编辑
- 图片变体生成
- 批量并发生成
- 图床上传
- 工作流编排
- 多服务商统一抽象

## 4. 集成方式

插件以“可复用本地插件”形式组织，而不是项目内写死脚本。

建议目录结构：

```text
fastaicode-image-mcp/
  .codex-plugin/
    plugin.json
  skills/
    fastaicode-image/
      SKILL.md
  server/
    __init__.py
    config.py
    models.py
    naming.py
    client.py
    mcp_server.py
  tests/
    test_config.py
    test_naming.py
    test_client.py
    test_mcp_tool.py
  examples/
    fastaicode-image.example.toml
```

说明：

- `plugin.json` 负责声明插件元数据与入口
- `server/` 承载 MCP server 代码
- `skills/` 承载配套 Skill
- `examples/` 放示例配置
- `tests/` 覆盖纯逻辑和工具入口

## 5. MCP Tool 设计

### 5.1 Tool 名称

- `generate_image`
- `edit_image`

### 5.2 输入参数

- `prompt: string`
  - 必填，文生图提示词
- `size_preset: string`
  - 可选，支持 `1k`、`2k`、`4k`、`auto`
  - 默认 `auto`
- `output_path: string`
  - 可选，若提供则直接保存到该路径
- `filename_hint: string`
  - 可选，用于补充输出文件名的可读摘要
- `model: string`
  - 可选，默认 `gpt-image-2`

### 5.3 返回结构

成功时返回结构化对象：

- `ok: true`
- `saved_path`
- `filename`
- `model`
- `size_preset`
- `resolved_request_size`
- `created`
- `revised_prompt`
- `source_image_path`（仅 `edit_image`）

失败时返回结构化对象：

- `ok: false`
- `error_code`
- `message`
- `details`

## 6. 配置设计

采用“配置文件 + 环境变量覆盖”。

配置项包括：

- `base_url`
- `api_key_env`
- `default_model`
- `default_output_dir`
- `size_preset_mapping`
- `request_timeout_seconds`

环境变量：

- `FASTAICODE_API_KEY`
- `FASTAICODE_BASE_URL`

默认规则：

- 未显式提供 `base_url` 时，读取配置文件
- 若设置了 `FASTAICODE_BASE_URL`，则覆盖配置文件值
- `api key` 不写入版本库，只从环境变量读取

## 7. 尺寸档位约定

对调用方暴露稳定档位，不暴露原始服务差异。

默认映射策略：

- `1k` -> `1024x1024`
- `2k` -> `auto`
- `4k` -> 高质量大图档位，由配置显式指定
- `auto` -> 不主动传 `size` 或传 `auto`，以配置为准

约束：

- 若 `4k` 在配置中未声明可用请求值，则直接报错
- 不允许静默把 `4k` 降级成 `2k` 或 `1k`
- 最终实际请求参数要回写到返回结构中的 `resolved_request_size`

## 8. 文件输出策略

默认输出目录：

- `outputs/images/`

命名规则：

- `YYYYMMDD-HHMMSS-slug.png`

其中：

- 时间戳必须存在，避免重名
- `slug` 来自 `filename_hint` 或 `prompt` 截断清洗
- 若 `output_path` 已提供，则优先使用 `output_path`
- 若目录不存在，则自动创建

## 9. 接口调用规范

目标接口：

- `POST /v1/images/generations`
- `POST /v1/images/edits`

请求体首版字段：

- `model`
- `prompt`
- `response_format`
- `size`（按档位解析后决定是否传入）

图生图首版字段：

- `model`
- `prompt`
- `image`

固定策略：

- `response_format` 首版固定为 `b64_json`
- 首版只支持 `png` 输出
- 返回里必须存在 `data[0].b64_json` 才视为成功
- `edit_image` 首版只支持本地 `input_image_path`
- 未来可扩展 URL、多图和 mask，但当前版本不实现

## 10. 错误处理

错误必须结构化，禁止只抛原始异常文本。

需要覆盖的场景：

- 缺少 `api key`
- 缺少或非法配置文件
- 请求超时
- 服务端返回非 200
- 返回体不是合法 JSON
- 返回体缺少 `data[0].b64_json`
- Base64 解码失败
- 目录创建失败
- 文件写入失败
- 请求了未配置的 `4k`

错误返回至少包含：

- `error_code`
- `message`
- `details`

## 11. Skill 设计

Skill 只负责指导，不直接发请求。

Skill 内容应明确：

- 什么时候优先调用 `generate_image`
- 什么时候优先调用 `edit_image`
- `1k`、`2k`、`4k`、`auto` 的含义
- 默认保存目录与命名方式
- 何时显式传入 `output_path`
- 常见失败排查顺序
- 当用户只说“帮我出图”时的推荐参数组织方式

Skill 必须把“执行请求”和“组织调用”边界讲清楚：

- MCP tool 负责执行
- Skill 负责规范使用

## 12. 测试与验证

### 12.1 自动化测试

至少覆盖：

- 尺寸档位映射
- 文件名生成
- 配置读取与环境变量覆盖
- 成功响应解析
- 错误响应解析
- Base64 图片落盘
- `multipart/form-data` 图生图请求
- `input_image_path` 缺失时的错误路径

测试中不依赖真实远端接口，使用 mock HTTP 响应。

### 12.2 手工验证

在具备真实 `api key` 的前提下，至少执行一次真实调用，验证：

- MCP tool 可被加载
- `generate_image` 可成功返回
- 图片成功保存到默认目录或显式路径
- 返回结果包含 `saved_path`

## 13. 实现约束

- 使用 `Python` 实现 MCP server
- 代码默认使用 ASCII
- 输出路径和配置解析要与 Linux 本地环境兼容
- 不把敏感信息写入仓库
- 首版只暴露一个 tool，避免接口膨胀

## 14. 验收标准

满足以下条件视为首版完成：

- Codex 可识别并调用本地 MCP tool `generate_image`
- 未传 `output_path` 时，图片默认落到 `outputs/images/`
- 传入 `output_path` 时，图片保存到指定位置
- 返回成功结构包含 `saved_path`、`model`、`size_preset`
- 常见失败能返回明确结构化错误
- Skill 能指导代理稳定使用该 tool
- 自动化测试通过
- 完成至少 1 次真实接口手工验证
