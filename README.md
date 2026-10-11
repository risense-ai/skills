# rsrs / respire · Skills

rsrs（Respire）技能库。每个技能是一个独立目录，含 **`SKILL.md`（必需）** + 可选 `scripts/`、`references/`。
可被 opencode 等支持 `SKILL.md` 约定的宿主加载：命中 `description` 里的触发词即自动调用。

---

## 目录结构

```
skills/
├─ README.md
└─ <skill-name>/
   ├─ SKILL.md            # 必需：frontmatter(name + description) + 正文
   ├─ scripts/            # 可选：可执行脚本
   └─ references/         # 可选：长文档 / 清单 / 手册
```

## SKILL.md 规范

```markdown
---
name: <skill-name>          # 小写连字符、与目录同名、≤64 字符
description: Use when …     # 必填；第三人称；把触发词前置（用户会说的词/文件名）
---

# <标题>

（正文：简明步骤；长内容放 references/，可执行逻辑放 scripts/）
```

- `description` 决定技能**何时被触发**：写清「做什么 + 何时用」，前置具体触发词，相邻主题用 "Use ONLY when…" 收窄。
- 正文保持精炼，把大块内容拆到 `references/`、把代码拆到 `scripts/`。

## 新增一个技能

1. 在仓库根建目录 `<skill-name>/`；
2. 写 `SKILL.md`（`name` = 目录名；`description` 前置触发词）；
3. 需要就加 `scripts/`、`references/`；
4. 在下文「技能清单」加一行；
5. 提交推送。

## 技能清单

| 技能 | 用途 | 触发词（示例） |
| --- | --- | --- |
| `memory-batch-tidy` | 一次性把 rsrs `extract` 导入的**会话摘要散根**批量收编入树（建归档锚 + `resort` 批量挂） | 批量整理提取的记忆 / 整理提取记忆 / 会话摘要散根归位 / 一键整理 extract 散根 / tidy extracted memories |

<!-- 新增技能时，在此表追加一行： | `<name>` | <用途> | <触发词> | -->

## 在 opencode 中启用

把本目录登记为一个技能搜索路径（全局或项目 `opencode.json(c)`），重启 opencode 生效：

```json
{
  "skills": {
    "paths": ["<本仓库 skills 目录的绝对路径>"]
  }
}
```

- opencode 会**递归**扫描该目录下的 `**/SKILL.md`。
- 也可把技能目录直接复制到默认扫描位 `~/.config/opencode/skills/`（或 `~/.agents/skills/`）。

## 验证是否加载

```bash
opencode debug skill
```

列出全部已加载技能的 `name / description / location`。**技能与配置只在 opencode 启动时载入，改后须重启 opencode / 开新会话**。

## 约定

- 一个技能一件事；目录名 = `name`。
- 不写入任何个人、设备、私有项目或密钥信息——本库面向所有使用者，保持通用可移植。
- 路径、命令尽量用占位符或自动探测，避免绑定特定环境。
