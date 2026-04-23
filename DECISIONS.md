# Decisions

## 2026-04-23: FastAICode 图片能力采用“本地 MCP 插件 + Skill”双层结构

结论：

- 使用可复用本地 `MCP server` 插件承载执行逻辑
- 使用配套 `Skill` 约束调用方式、档位语义和错误处理

原因：

- `MCP` 负责执行，便于让 Codex 直接调用
- `Skill` 负责规范使用，避免把接口细节散落到对话里
- 后续加图片编辑或更多工具时，结构可继续扩展

影响范围：

- 插件需包含 `.codex-plugin/plugin.json`、MCP server 实现、Skill 文档、配置示例和测试
- 首版暴露 `generate_image` 与 `edit_image`

## 2026-04-23: GitHub 发布整理采用“根级入口文档 + 插件内细节文档 + 便携 `.mcp.json`”三层交付

结论：

- 根目录负责说明仓库用途、结构和发布注意事项
- 插件目录负责说明 `MCP` 结构、安装方式、参数和部署步骤
- `.mcp.json` 不再写死当前机器的绝对路径，默认改成可移植的相对路径写法

原因：

- GitHub 访客先看到的是根目录，需要一个清晰的入口
- 插件真实用法集中在子目录，更适合放详细部署文档
- 绝对路径配置不适合公开仓库复用

影响范围：

- 需要新增根级 `README.md`、`.gitignore`、`LICENSE` 占位和 `CI workflow`
- 需要新增 `fastaicode-image-mcp/README.md` 与 `.env.example`
- 需要在文档里明确说明相对路径与绝对路径两种注册方式
