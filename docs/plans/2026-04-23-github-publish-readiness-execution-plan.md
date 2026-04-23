# GitHub Publish Readiness Execution Plan

日期：2026-04-23

## Goal

把现有 `fastaicode-image-mcp` 整理成一个对 GitHub 读者友好、对 MCP 使用者可复现的仓库。

## Internal Grade

`M`

原因：本次主要是文档、配置和发布整理，不涉及多代理或大规模实现。

## Step 1: 根级入口与忽略规则

- 创建 `README.md`
- 创建 `.gitignore`
- 创建 `LICENSE` 占位文件
- 创建 `.github/workflows/ci.yml`

## Step 2: 插件级说明与可移植配置

- 创建 `fastaicode-image-mcp/README.md`
- 创建 `fastaicode-image-mcp/.env.example`
- 修改 `fastaicode-image-mcp/.mcp.json`
- 更新 `fastaicode-image-mcp/.codex-plugin/plugin.json`

## Step 3: 状态与治理产物

- 更新 `CURRENT_TASK.md`
- 更新 `DECISIONS.md`
- 写入本次 requirement / runtime receipts

## Verification

执行以下命令：

```bash
pytest fastaicode-image-mcp/tests -v
python3 fastaicode-image-mcp/server/mcp_server.py
```

第二条命令在无输入时应直接退出，不应抛异常。

## Rollback

- 如 README 或 `.mcp.json` 说明与实际运行不一致，优先回滚文档与配置变更，不动核心服务代码
- 如 `CI` 失败，仅调整 workflow，不改业务逻辑

## Cleanup

- 保持生成图片目录被 `.gitignore` 忽略
- 不提交本机私有环境变量
- 用 runtime receipt 记录本次验证结果
