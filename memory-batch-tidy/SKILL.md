---
name: memory-batch-tidy
description: Use when the user wants to bulk-tidy in ONE pass the many session-summary root entries that rsrs "extract" (session import) creates — triggers "批量整理提取的记忆", "整理提取记忆", "会话摘要散根归位", "一键整理 extract 散根", "整理导入的会话记忆", "tidy extracted memories", "bulk tidy session imports". Builds theme archive anchors under a chosen tree root, then batch-attaches the root session summaries with `resort`. Environment-agnostic.
---

# 批量整理「提取记忆」（会话摘要散根）

## 何时用
用户跑过 `rsrs extract`（会话导入）之后，库里会出现**大量无父的会话摘要根**（散根），想**一次性**把它们收编进知识树。适用于本人库的存量散根，也适用于把记忆迁移到新库后的批量归位。

## 前置
- `rsrs` CLI 可用。受限/沙盒环境所有命令加 `--client-only`（仅连宿主 loopback runtime）；普通环境直接跑 `rsrs`。
- 任何写入前**先备份**（见步骤 3）。

## 流程（默认 dry-run，确认后再落库）
1. **摸底**：`rsrs status`、`rsrs resort --status`（TIDY 计数）、`rsrs tree-cure`（roots / lone leaf）。
2. **诊断**：`rsrs audit --json`（孤儿/截断题/同名/深链）；`rsrs defrag`（相似簇——**多为假阳性，勿按簇动手**）。
3. **备份**：`rsrs export <持久目录>/memories_YYYYMMDD.json`。
4. **建归档锚**（一个主题/项目一个锚）：
   `rsrs remember "<一句说明>" --title "会话归档：<主题>" --type context --importance important --parent <树名或id> --json`
   `--parent` 接受 id / 前 8 位 / 树名；锚是归档容器，**必须带 `--parent`，不得裸存成根**。
5. **批量挂**：编辑 `scripts/tidy_extracted.py` 顶部配置（`PREFIXES`、`TARGET_ROOT`、`ANCHORS` 换成你的项目关键词），然后
   `python scripts/tidy_extracted.py`（预览分布与 moved）→ 确认 → `python scripts/tidy_extracted.py --go`。
6. **复验**：`rsrs audit --json`（orphans=0、truncated=0）、`rsrs tree-cure`（lone leaf 归零）、`rsrs resort --status`（PASS）。

## 验收标准
`roots` 明显下降、`lone leaf → 0`、`orphans=0`、TIDY 计数复位。各锚子条数之和 = 本次挂入的散根数。

## 关键坑
- `resort --go` 会**顺带复位 TIDY 计数**，无需再 `--reset`。
- **同名组多为假阳性**（摘要共用样板首行），不是真重复；defrag 的相似簇亦多假阳性，禁按簇合并。
- 批量挂**先 dry-run**；spec 过大（约 300 条以上）分块。
- 若同一轮还做**真重复合并**（`remember --merge-ids`）：合并会删旧条 → **先查子条、并后立即把孤儿子条改挂到新条**。
- 在 PowerShell 里给 `resort --spec` 传含引号的 JSON 易丢引号 → 用脚本（Python `subprocess` 列表传参）最稳；Python 打印中文前先 `sys.stdout.reconfigure(encoding='utf-8')`。

完整操作手册见 `references/operations.md`；可执行脚本见 `scripts/tidy_extracted.py`。
