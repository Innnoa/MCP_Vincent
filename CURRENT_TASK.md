# Current Task

日期：2026-04-23

## 目标

将当前仓库整理为可上传到 GitHub 的可复用项目，补齐发布必需文件，并把现有 `MCP` 结构、使用方法和部署方式写清楚。

## 范围

- 新增根级 `README.md`
- 新增根级 `.gitignore`
- 新增根级 `LICENSE` 占位文件
- 新增 `.github/workflows/ci.yml`
- 新增 `fastaicode-image-mcp/README.md`
- 新增 `fastaicode-image-mcp/.env.example`
- 将 `fastaicode-image-mcp/.mcp.json` 改成更可移植的写法
- 写入本次 GitHub 发布整理的 requirement / plan / runtime receipt

## 验收标准

- 根级 README 能说明仓库用途、结构和发布前注意事项
- 插件目录 README 能说明 `MCP` 结构、参数、部署与验证方式
- `.gitignore` 能排除本地缓存、密钥文件和生成图片
- `.mcp.json` 不再写死当前机器绝对路径
- `pytest fastaicode-image-mcp/tests -v` 通过

## 当前状态

- GitHub 发布所需说明文件已补齐
- `.mcp.json` 已改为相对路径写法，去掉当前机器绝对路径
- `pytest fastaicode-image-mcp/tests -v` 已通过
- `python3 fastaicode-image-mcp/server/mcp_server.py` 已验证可在无输入时正常退出
- 首个提交已创建并推送到 `origin/main`

## 相关文件

- `README.md`
- `.gitignore`
- `.github/workflows/ci.yml`
- `fastaicode-image-mcp/`
- `docs/requirements/2026-04-23-github-publish-readiness.md`
- `docs/plans/2026-04-23-github-publish-readiness-execution-plan.md`
- `outputs/runtime/vibe-sessions/20260423-github-publish-readiness/`

## 下一步

1. 选择最终许可证并替换根目录 `LICENSE`
2. 按实际宿主环境确认 `.mcp.json` 是否需要切换为绝对路径
3. 如需公开给他人复用，可再补仓库标签、Release 和示例截图
