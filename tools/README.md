# 「十二飞鸟」剧本自动化工具集

> 四个工具覆盖剧本创作的 **生成→Review→转CSV→伏笔追踪** 完整流水线。

---

## 环境要求

- **Python 3.8+** （需要安装，可从 https://www.python.org/downloads/ 下载）
- 所有工具使用标准库，**无需额外安装第三方包**

---

## 工具一览

| 工具 | 功能 | 输入 | 输出 |
|------|------|------|------|
| `event_skeleton.py` | 骨架生成 | 60天规划文档 | Day骨架模板.txt |
| `auto_review.py` | 自动Review | 文字剧本.txt / CSV剧本.csv | 检查报告 |
| `txt_to_csv.py` | 文字→CSV转化 | 文字剧本.txt | CSV剧本.csv |
| `foreshadow_tracker.py` | 伏笔追踪 | 剧本目录 / 手动 | 伏笔数据库.json |

---

## 推荐工作流程

```
  Day N的规划
      │
      ▼
  [1] event_skeleton.py Day N    ──→  生成骨架模板
      │
      ▼
  [2] 人工创作文字剧本（参考骨架）
      │
      ▼
  [3] auto_review.py 剧本.txt    ──→  自动检查8项
      │
      ▼
  [4] txt_to_csv.py 剧本.txt     ──→  半自动转CSV
      │
      ▼
  [5] 人工标注CSV演出指令
      │
      ▼
  [6] foreshadow_tracker.py      ──→  追踪伏笔兑现
```

---

## 详细用法

### 1. event_skeleton.py — 骨架生成

```bash
# 生成 Day 20 的创作骨架（打印到屏幕）
python tools/event_skeleton.py 20

# 生成 Day 5~10 的骨架并保存到文件
python tools/event_skeleton.py 5-10 --output ./骨架/

# 生成全部60天骨架
python tools/event_skeleton.py 1-60 --output ./骨架/

# 查看全剧概览
python tools/event_skeleton.py overview

# 指定规划文档路径
python tools/event_skeleton.py 20 --plan ./设定文档/剧本规划_60天完整版.txt
```

**骨架模板包含：**
- 事件编号、时段、类型标记（★关键/⭐好感度/↪过渡/☠BE）
- 出场角色及红线提醒
- 场景地点猜测
- 创作提示
- 可直接填充的剧本框架

---

### 2. auto_review.py — 自动Review

```bash
# Review 文字剧本
python tools/auto_review.py ./文字剧本/Day20剧本.txt

# Review CSV 剧本
python tools/auto_review.py ./csv剧本/Day_4_afternoon_BedStore.csv

# 严格模式（警告也报错）+ 输出报告
python tools/auto_review.py ./文字剧本/Day20剧本.txt --strict --output review_report.txt
```

**8项检查清单：**
1. ✅ 日语残留检测（假名/片假名/日语词汇）
2. ✅ 格式合规（事件分割/地点标记/Speaker格式）
3. ✅ 角色名一致性（简称vs全名）
4. ✅ POV合规（主角活动范围/禁地）
5. ✅ BE标记格式（触发点+完整分支）
6. ✅ 角色设定红线（每个角色的禁止事项）
7. ✅ 禁止文艺比喻（煽情比喻检测）
8. ✅ 主角台词字数（≤15字限制）

---

### 3. txt_to_csv.py — 文字→CSV转化

```bash
# 转化Day3剧本
python tools/txt_to_csv.py ./文字剧本/Day3剧本.txt ./csv剧本/

# 指定输出目录
python tools/txt_to_csv.py ./文字剧本/Day20剧本.txt ./csv剧本/Day20/
```

**转化规则：**
- `【旁白】` → `Speaker: hide`（环境叙述/心理活动）
- `【角色名】` → `Speaker: 角色全名`（自动匹配映射表）
- `【我】` → （主角内容，标记为narration）
- 自动猜测 Background / BGM
- ID 格式与现有规则一致（10[Day][Event][序号]）

**⚠ 需要人工标注的字段：**
- `HeadProfile` — 角色立绘ID（如 `YukiyoKatsurahara_work`）
- `CharLeft / CharMid / CharRight` — 立绘位置
- `Background / BGM` — 精确场景/音乐（自动猜测仅供参考）
- `Voice` — 语音指令
- `Command` — 特殊指令（loadScript / choice / AddS_Char / bgfade）

---

### 4. foreshadow_tracker.py — 伏笔追踪

```bash
# 扫描目录下所有剧本发现伏笔
python tools/foreshadow_tracker.py scan ./文字剧本/

# 检查 Day 14 的伏笔兑现情况
python tools/foreshadow_tracker.py check 14

# 生成全剧伏笔状态报告
python tools/foreshadow_tracker.py report

# 手动添加伏笔
python tools/foreshadow_tracker.py add "育子在Day9的来信中提到想学化妆" 9 13

# 查询伏笔
python tools/foreshadow_tracker.py query "草莓"
```

**伏笔数据库** (`foreshadow_db.json`) 包含15条预登记伏笔：
- 草莓布丁、加蛋、增田烧酒、墙纸意象
- E-04药瓶、黑皮书、Phoenix Coin
- 绳索理论、佐藤倒计时等

---

## CSV 格式说明（不改变）

所有CSV保持12列标准格式：

```
ID,Speaker,HeadProfile,CharLeft,CharMid,CharRight,Text,Background,BGM,Voice,Command,Note
```

| 列 | 说明 | 示例 |
|----|------|------|
| ID | 唯一标识 `10[Day][Event][序号]` | `10100001` |
| Speaker | 说话人/hide（旁白） | `白鹤姬·桂原雪代` 或 `hide` |
| HeadProfile | 立绘ID | `hide` / `YukiyoKatsurahara_work` |
| CharLeft | 左侧立绘 | `hide` / 立绘ID |
| CharMid | 中间立绘 | `hide` / 立绘ID |
| CharRight | 右侧立绘 | `hide` / 立绘ID |
| Text | 文本内容 | `夕阳将天空染成暗金与绛紫的渐变色。` |
| Background | 背景场景 | `Corridor` / `Jan_Room` |
| BGM | 背景音乐 | `Unreal_Memory` / `Slow_Lure` |
| Voice | 语音文件 | （通常为空） |
| Command | 引擎指令 | `loadScript(...)` / `choice(...)` |
| Note | 备注 | 自由文本 |

---

## 文件结构

```
十二飞鸟_codebuddy/
├── tools/
│   ├── README.md              ← 本说明
│   ├── event_skeleton.py      ← 骨架生成器
│   ├── auto_review.py         ← 自动Review
│   ├── txt_to_csv.py          ← 文字→CSV转化
│   ├── foreshadow_tracker.py  ← 伏笔追踪
│   └── foreshadow_db.json     ← 伏笔数据库（自动创建）
├── 文字剧本/
├── csv剧本/
└── 设定文档/
```
