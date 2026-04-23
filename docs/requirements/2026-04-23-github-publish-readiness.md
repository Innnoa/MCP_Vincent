# GitHub Publish Readiness Requirements

日期：2026-04-23

## 1. 目标

将当前 `Vincent` 仓库整理成可以上传到 GitHub 的可复用项目，让外部使用者能够快速理解：

- 仓库是做什么的
- 当前 `MCP` 结构如何组织
- 如何本地安装、配置和部署
- 如何验证插件是否正常工作

## 2. 当前基础

仓库当前已经包含一个可运行的本地插件子目录 `fastaicode-image-mcp/`，内部已有：

- `.codex-plugin/plugin.json`
- `.mcp.json`
- `server/`
- `skills/`
- `tests/`
- `fastaicode-image-mcp.toml`

当前缺口主要在“发布可读性”和“部署可移植性”，不是业务逻辑缺失。

## 3. 本次范围

- 新增根级 `README.md`
- 新增根级 `.gitignore`
- 新增根级 `LICENSE` 占位文件
- 新增 GitHub Actions `CI`
- 新增 `fastaicode-image-mcp/README.md`
- 新增 `fastaicode-image-mcp/.env.example`
- 把 `fastaicode-image-mcp/.mcp.json` 调整为更可移植的写法
- 写入本次整理的 plan 与 runtime receipt

## 4. 验收标准

- 仓库根目录能独立说明项目用途与入口
- 插件目录能独立说明结构、配置、工具参数和部署步骤
- 本地路径不再写死为当前机器的仓库绝对路径
- `.gitignore` 能避免缓存、密钥和生成图片进入版本库
- 现有测试命令 `pytest fastaicode-image-mcp/tests -v` 通过

## 5. 约束

- 不改动核心工具行为与接口命名
- 不假定仓库所有者已经决定最终开源许可证
- 不引入新的远端依赖或新的运行时要求

## 6. 非目标

- 不新增图片功能
- 不重构插件内部模块
- 不实现多图输入、URL 输入或 mask
- 不代替仓库所有者做最终许可证选择
