# 批量整理「提取记忆」操作手册（通用版）

> 一次性把 `rsrs extract` / 会话导入（session import）产生的大批**会话摘要散根**收编进知识树。
> 本文为**环境无关**版本：命令与脚本都用占位符书写，替换成你自己的值即可；不含任何个人/设备/项目/记忆 ID 信息。

---

## 0. 一句话

`extract` 为每个 IDE / Agent 会话生成一条摘要记忆（默认 `important`、**无父**）→ 批量导入后，整库会多出成百条**散根**（root，无父节点）。本流程按「工作目录 + 关键词」把它们**确定性分组**，在目标树根下建若干**归档锚**，再一次 `resort` 批量挂入；**先 dry-run、可回滚、不依赖任何模型**。

> 适用：本人库的存量散根；或将记忆迁移到新库后，把导入条目批量归位。

---

## 1. 原理与背景

- `rsrs extract`（会话导入，支持多平台）为每个会话生成一条摘要，正文形如：
  `【前因】<平台> 会话 <会话id>。起始 …；工作目录 <工作目录>；模型 <模型>。【行为】<首条指令> …【后果】会话更新于 …。`
  默认 `--importance important`，且**未解析父节点** → 全部成为根节点（散根）。
- 这类根**不算孤儿**：`audit` 的 orphans 指「父 id 悬空」，根节点不计入，故 `audit` 可能全绿而树很碎。
- 内置梳理**不会自动挂**它们：
  - `classify --plan`（纯本地）不做语义归类 → 通常 `proposed 0`；
  - `classify --tree --auto` 需先配置**分类后端**（`classify --ds <key>`），否则不可用。
- 因此采用**确定性收编**：规则分类 → 建归档锚 → `resort` 批量挂。**无需模型、可逆**。

---

## 2. 前置检查

```bash
rsrs status            # data_dir / 条数 / 设备
rsrs resort --status   # TIDY 计数（是否需要整理）
rsrs tree-cure         # roots 数量 + lone-leaf 挂载建议
```

- 受限/沙盒环境：以上命令与后续所有命令都加 `--client-only`。
- 先核对 `data_dir`，**勿照搬他人路径**。

---

## 3. 五步流程

### 步骤 1 · 取数（圈定本次对象）

```bash
# 自上次梳理后新增（缺省口径）：
rsrs list --since-resort --limit 500 --json
# 全库（同一入口，换时间下界）：
rsrs list --since 1900 --limit 5000 --json
```

- 该输出只含**短 id + 标题**，不含父/重要性；需要细节时用 `show <id> --json`。
- 若用 PowerShell 把输出重定向到文件，会写成 UTF-16；用 Python 解析要 `encoding='utf-16'`，或干脆让脚本自己调 CLI（见第 5 节）。

### 步骤 2 · 诊断

```bash
rsrs audit --json     # 孤儿 / 非法值 / 同名组 / 截断题 / 最大深度
rsrs tree-cure        # roots 数 + lone-leaf 挂载建议
rsrs defrag           # 相似簇（多为假阳性，勿按簇动手）
```

判读要点：
- **同名组**（`same_title_groups`）：会话摘要常共用样板首行 → 多为**假阳性**，不是真重复。
- **defrag 簇**：分类根、同句式异章节、同树异枝 → **一律假阳性，禁并**。
- 真正该动手的：**真重复条**（同一件事的多条散讲）、**错挂/断链**、**散根**（本文重点）。

### 步骤 3 · 备份（写入前必做）

```bash
rsrs export <持久目录>/memories_YYYYMMDD.json
```

导出全库明文快照。**放持久目录**，勿放临时目录；库无版本历史，`update`/`merge` 不可逆。

### 步骤 4 · 建归档锚

在目标树根下建若干**归档容器**（一个项目/主题一个锚），供散根下挂：

```bash
# 示例：给「某项目」的会话摘要建一个锚（挂在 rsrs 内置分类「编程开发」下）
rsrs remember "<一句话说明此锚用途>" \
  --title "会话归档：<某项目>" \
  --type context --importance important \
  --parent 编程开发 --json
```

- `--parent` 支持 **id / 前 8 位 / 树名**。
- 锚标题即锚名（尽量 ≤80 字）；**不得裸存成根**：必须带 `--parent`。
- 锚只是**归档容器**，不是新建「纲」（新建纲须用户显式同意后 `root-create --yes`）。

### 步骤 5 · 分类映射（确定性规则）

对每条散根，按 **工作目录 → 项目关键词** 决定归属锚。填进脚本 `ANCHORS` 的规则形如：

| 归档锚 | 命中规则（标题/正文含，或工作目录含） | 说明 |
|---|---|---|
| 会话归档：项目A | `项目A` 的独有关键词 | |
| 会话归档：项目B | `项目B` 的独有关键词 | |
| 会话归档：其他 | 以上皆不中 | 兜底 |

> 规则**从具体到宽泛**排列（具体项目要先于通用词判断，否则会串类）。
> 若多数条目的「工作目录」缺失（导出的摘要里常写「未知」），就以**标题/正文关键词**为主，命不中的进「其他」兜底锚。

### 步骤 6 · 批量挂（先 dry-run）

`resort --spec` 接受 `id / 前 8 位 / 树名`；**默认 dry-run**，加 `--go` 才写入，并**顺带复位 TIDY 计数**。

```bash
# spec 形如： {"ops":[{"id":"子短id","parent":"锚短id"}, ...]}
rsrs resort --spec '<JSON>' --json          # dry-run：status=pending, moved=N
rsrs resort --spec '<JSON>' --go --json     # 落库：status=ok, moved=N, counter=reset
```

- 单条 spec 约几十字节、数百条约几十 KB；接近命令行长度上限（Windows ~32 KB）时**分块**（每 ~300 条一次）。
- PowerShell 传含引号的 JSON 易丢引号 → **用第 5 节的 Python 脚本**最稳。

### 步骤 7 · 复验（必做）

```bash
rsrs audit --json      # 期望：orphans=0、truncated=0
rsrs tree-cure         # 期望：lone leaf 大幅下降/归零
rsrs resort --status   # 期望：PASS（计数已复位）
rsrs tree --outline --json   # 目视各锚下的子条数
```

**验收标准**：`roots` 明显下降、`lone leaf → 0`、`orphans=0`、TIDY 复位；各锚子条数之和 = 本次挂入的散根数。

---

## 4. 命令速查

| 目的 | 命令 |
|---|---|
| 取数（批次 / 全库） | `rsrs list --since-resort --limit 500 --json` · `rsrs list --since 1900 --limit 5000 --json` |
| 诊断 | `rsrs audit --json` · `rsrs tree-cure` · `rsrs defrag` |
| 备份 | `rsrs export <目录>/memories_YYYYMMDD.json` |
| 建锚 | `rsrs remember "<说明>" --title "会话归档：X" --importance important --parent <树名|id> --json` |
| 批量挂 | `rsrs resort --spec '<JSON>' --json`（预览）→ 加 `--go`（落库+复位计数） |
| 复位计数 | `resort --go`（随批量）或 `rsrs resort --reset` |
| 看节点 | `rsrs show <id> --json` · `rsrs tree --from <id> --depth 3 --json` |

---

## 5. 一键脚本（`scripts/tidy_extracted.py`）

与 rsrs 同机运行，**默认 dry-run**，确认无误再加 `--go`。

- 顶部 **配置区**改成你自己的值：
  - `PREFIXES` —— 视为散根的标题前缀（若导入条目带 `session-import` 之类的 tag，脚本会优先按 tag 识别，前缀作兜底）；
  - `TARGET_ROOT` —— 归档锚挂在哪个树根下（用 rsrs 内置分类名或节点 id）；
  - `ANCHORS` —— 主题 → 关键词规则（最后一条 `OT` 作兜底，勿删）。
- 脚本会：导出快照 → 找出无父的散根 → 按规则分类 → 建/复用锚 → 组 `resort --spec` → 预览或落库。

```bash
python scripts/tidy_extracted.py            # 预览：散根数 / 分布 / dry-run moved
python scripts/tidy_extracted.py --go       # 确认后落库
# 路径/环境特殊时：
python scripts/tidy_extracted.py --rsrs <rsrs可执行文件> --client-only --backup <快照路径>
```

---

## 6. 常见坑

1. **先 dry-run**：`resort` 缺省不写；看到 `status=pending, moved=N` 再 `--go`。
2. **`resort --go` 会复位 TIDY 计数**（`counter=reset`）——这是预期，不必再 `--reset`。
3. **同名 ≠ 真重复**：摘要共用样板首行，`same_title_groups` 多为假阳性。
4. **defrag 簇多为假阳性**：分类根/同句式异章节/同树异枝一律禁并。
5. **合并必查子孙**：若做真重复合并（`remember --merge-ids`），合并删旧条 → 先查子条、并后立即把孤儿子条改挂到新条。
6. **传参引号**：PowerShell 给原生程序传含引号的 JSON 易丢 → 走 Python `subprocess` 列表传参。
7. **控制台编码**：Windows 上 Python 默认 cp1252，打印中文会崩 → 先 `sys.stdout.reconfigure(encoding='utf-8')`（或设 `PYTHONIOENCODING=utf-8`）。
8. **批次过大**：spec 超约 300 条建议分块；导出/备份放持久目录。

---

## 7. 回滚

- **改挂可逆**：把子条 `resort` 改回原父（或目标树根）即可；或按步骤 3 的快照对照重放。
- **删锚**：锚空了可 `rsrs forget <锚id>` 软删（可 `rsrs restore <完整id>` 恢复）。
- **全量还原**：以导出快照为准（本地库无版本历史，`update`/`merge` 不可逆 → **动前必备份**）。

---

## 8. 备注

- 若 `extract` 已内置「无父时默认挂某树根」的防散根加固，则**新导入不再产生散根**；本流程主要用于**存量散根**与**他库迁移**。
- 想更省事可用模型做语义归类（`classify --tree --auto`，需先配置分类后端）；本文的**确定性收编**无需模型、可复现，二者可互补。
