# 绘图提示词包（可直接复制给 Gemini）

> 对齐 `docs/01-资产清单与预算.md` 的规格。出图提示词用英文更稳，中文只作说明。
> 本文件覆盖 P0 全部绘图需求：角色 → 背景 → 材料道具 → UI → 图标。
> **交付前先看第 6 节的命名对照表。**

## 0. 通用出图流程

1. 用 **Base Character Card** 生成 `calm`，反复刷到满意（良品率约 1/10，刷 15–30 张正常）。
2. 把满意的 `calm` **作为参考图**派生其余 4 个表情，每次只改那一句表情描述。
3. 背景同理：先出一张定死透视与光线，其余场景沿用同一套光线描述词。
4. 道具与 UI **不要一次生成一堆**：一张一张来，命名对了再生成下一张。

---

## 1. Base Character Card（先生成这一张：calm）

```
Semi-realistic digital illustration, waist-up portrait of a 42-year-old East Asian male consular officer,
three-quarter view facing slightly toward camera-left, looking at the viewer.
Dark navy wool suit jacket, crisp white dress shirt with open collar, no tie, no pocket square.
Short black hair neatly combed with a few grey strands at the temples, clean-shaven with a faint stubble shadow.
Sharp narrow eyes, visible under-eye lines, thin lips, high cheekbones, slightly hollow cheeks. Tired but highly attentive.
Expression: completely neutral and unreadable — level gaze, relaxed eyebrows, mouth closed in a flat line.
Plain cool grey-blue wall far behind, softly out of focus. Soft directional window light from the left, gentle shadow on the right side of the face.
Cool desaturated palette, clean confident line art, subtle stylization, cinematic, high facial detail.
Vertical composition, head near the top third, plain uncluttered background, nothing in the foreground.
```

**Negative prompt**

```
text, watermark, logo, signature, frame, border, anime style, chibi, big cartoon eyes, exaggerated proportions,
smile, grin, teeth showing, hat, sunglasses, beard, moustache, earrings, jewelry, bright saturated colors,
busy background, office furniture, desk in foreground, crowd, other people, full body, cropped head,
extra fingers, deformed hands, distorted face, asymmetric eyes, plastic skin, heavy makeup
```

## 2. 五个表情（用 calm 作参考图逐张派生）

| 文件名 | 表情 | 追加指令（替换那一句） |
|---|---|---|
| `officer_calm.png` | 平静审视 | `Change ONLY the facial expression to: completely neutral and unreadable — level gaze, relaxed eyebrows, mouth closed in a flat line.` |
| `officer_doubt.png` | 轻微怀疑 | `Change ONLY the facial expression to: one eyebrow slightly raised, eyes narrowed a fraction, head tilted about three degrees, lips pressed together, skeptical squint.` |
| `officer_impatient.png` | 明显不耐烦 | `Change ONLY the facial expression to: brows lowered and drawn together, jaw tense, eyes cast down toward unseen documents, one hand raised palm-down as if cutting the conversation short.` |
| `officer_interested.png` | 突然感兴趣 | `Change ONLY the facial expression to: eyebrows lifted, eyes widened with genuine curiosity, head raised, leaning slightly forward, the first hint of a smile at one corner of the mouth.` |
| `officer_caught.png` | 冷笑 / 识破 | `Change ONLY the facial expression to: cold knowing smirk, one eyebrow raised high, eyes hard and amused, chin slightly lifted, as if he has just caught a lie.` |

**强度要求**：`doubt` 与 `impatient` 必须一眼可辨（这是玩家判断处境的仪表盘）；
`interested` 与 `caught` 是全局最夸张的两张 —— 一个是奖励，一个是惩罚。

## 3. 背景（3 张，1920×1080）

### `room_interview.png` —— 面试室 · 主战场
```
Semi-realistic digital illustration of a consulate visa interview room, seen from the applicant's seated eye level.
A wide dark counter runs across the lower third, mostly empty except a small lamp, a stamp pad and a stack of folders.
Behind the desk: a plain cool grey-blue wall, a frosted glass partition, a small flag on a short pole at the far right.
Overhead fluorescent lighting plus soft daylight from a high window on the left. Muted cool palette, low contrast so a character can stand in front.
Slightly desaturated, cinematic, clean line art, no people, no text. Leave the lower 320 pixels visually quiet (a dialogue box covers them).
```

### `room_docs.png` —— 文件整理室 / 桌面（开场独立解谜场景）
```
Semi-realistic digital illustration, close top-down-angled view of a cluttered hotel desk at night.
Scattered blank passport pages, bank statements, a pair of scissors, a glue stick, a desk lamp casting a warm pool of light,
a laptop edge just visible at the top of the frame, a coffee cup ring stain. Warm tungsten light fading into deep shadow at the edges.
Tense, quiet, slightly noir atmosphere. Clean line art, no readable text on any paper, no people. Leave the lower 320 pixels visually quiet.
```

### `hall_embassy.png` —— 大使馆走廊 / 等候区
```
Semi-realistic digital illustration of a long embassy corridor and waiting area, one-point perspective.
Rows of empty grey plastic chairs on the left, a queue rope, a numbered display panel on the wall (blank screen, no text),
fluorescent ceiling lights receding into the distance, a large window at the far end with cold daylight.
Cool desaturated palette, slight unease, institutional. Clean line art, no people, no text. Leave the lower 320 pixels visually quiet.
```

## 4. 材料道具图（6 张，卡牌中央的物品特写）

统一要求：**正面或微俯视、浅景深、柔和的顶光、桌面纹理可见、透明底或极简纯色底**，
重要：**所有印刷文字必须渲染成不可辨认的模糊墨迹** —— 不出现可读姓名、真实机构名、国徽或任何真实证件模板。

```
Close-up product-style illustration of a single <OBJECT> lying flat on a dark wooden desk,
photographed from slightly above at a 15-degree angle, soft diffused overhead light, shallow depth of field,
crisp paper edges, subtle drop shadow, muted realistic color, clean line art, semi-realistic style,
all printed text rendered as illegible blurred ink smudges, no readable names, no logos, no emblems,
no hands, no people, centered composition, transparent background
```

把 `<OBJECT>` 换成下面每一项：

| 文件名 | `<OBJECT>` 替换为 | 额外要求 |
|---|---|---|
| `item_passport.png` | `a closed dark blue passport booklet with a worn cover` | 不要国徽；封面是抽象压纹 |
| `item_invitation.png` | `a single sheet of letterhead paper with a formal layout, slightly creased` | 底部有一块**干净的空白**（暗示没盖章） |
| `item_bank_statement.png` | `a printed bank transaction statement with dense tabular rows, three highlighted lines` | 三行用荧光笔标出（叙事上就是那三笔现金） |
| `item_bank_statement_clean.png` | `the same bank statement, freshly printed, neat and flat, no highlighting` | 与上一张**同一张纸的整洁版**，方便玩家对比 |
| `item_employment.png` | `a formal certificate of employment on company letterhead with a red seal stamp at the bottom right` | 印章要**模糊不可辨** |
| `item_hotel_booking.png` | `a printed hotel booking confirmation with a barcode block and a date table` | 日期区域清晰（玩家要看得出"日期不对"） |

## 5. UI 套件（9-slice 与按钮）

> 诚实建议：**图标不要去生成**，直接用开源图标集（Lucide / Phosphor，MIT 许可）改色即可，
> 省时且风格统一。UI 底图建议 AI 出母版 + 手动切九宫格，一次成型后复用。

### 5.1 对话框底（母版 2400×700）
```
Game UI asset, a wide horizontal dialogue box panel, deep desaturated charcoal navy, 92% opacity,
thin cool-grey 2px inner border, subtle paper grain texture, softly rounded 24px corners, matte finish,
no text, no icons, no character art, flat orthographic front view, centered, isolated on transparent background
```

### 5.2 选项按钮（母版 1200×120，出 4 态）
母版：`a horizontal rounded-rectangle UI button, dark slate fill, 1px cool grey border, soft inner glow at the top edge, no text, isolated on transparent background`
四态靠微调：常态(基础) / 悬停(`brighten the border and add a faint warm rim light`) / 选中(`filled with a muted warm sand tone, text area darker`) / 禁用(`fully desaturated grey, 40% opacity, border dashed`)。

### 5.3 怀疑度计（1400×60，5 段）
```
Game UI asset, a horizontal segmented gauge with five equal segments separated by thin 2px dividers,
segments colored from calm cool teal to cold grey to warning amber to dull red, flat design, subtle bevel,
no text, no numbers, no icons, isolated on transparent background
```

### 5.4 材料卡牌（260×340，3 态）
```
Game UI asset, a vertical trading-card frame, dark paper texture with a thin metallic border and a small header band,
empty center window for an item image, no text, no icons, isolated on transparent background
```
三态：拥有(基础) / 已提交(`add a soft warm seal glow at the bottom edge`) / 已击穿(`a bold red diagonal cross over the whole card, desaturated`)。

### 5.5 模态解谜框（1600×1000）
```
Game UI asset, a large modal dialog panel with a slightly industrial look, dark grey metal and frosted glass,
a header strip on top, a recessed central work area, corner rivets, cool rim lighting,
no text, no icons, isolated on transparent background
```
配套全屏遮罩：`a plain black semi-transparent overlay at 55% opacity`（可直接用纯色层，不必出图）。

### 5.6 结局图章（500×500，3 枚）
```
A single ink rubber-stamp impression, slightly misaligned and unevenly inked, authentic worn texture,
transparent background, no other elements
```
三枚的颜色与文字（**这一处允许出现文字**，是游戏自造的虚构图章）：`APPROVED` 深绿 / `DENIED` 暗红 / `221(g)` 琥珀色（行政审查）。


## 6. 交付对照表（做完照着核对）

| 目录 | 文件 | 数量 |
|---|---|---|
| `assets/characters/officer/` | `officer_{calm,doubt,impatient,interested,caught}.png` | 5 |
| `assets/backgrounds/` | `room_interview.png`、`room_docs.png`、`hall_embassy.png` | 3 |
| `assets/items/` | `item_{passport,invitation,bank_statement,bank_statement_clean,employment,hotel_booking}.png` | 6 |
| `assets/ui/` | 见 5.1–5.6（对话框 / 按钮 ×4 / 怀疑度计 / 卡牌 ×3 / 解谜框 / 图章 ×3） | 13 |

**自检清单**

- [ ] 5 张表情并排看：同一个人，情绪无需文字说明就能分辨
- [ ] 缩到 1280×720 仍然清楚
- [ ] 立绘底部 320 px 没有重要内容
- [ ] 透明底干净，200% 放大没有白边
- [ ] 道具图上**没有任何可辨认的文字或真实机构标识**
- [ ] 文件名 = 内容 id，一个字母都不能差（引擎按 id 找图）

---

## 7. 第一轮出图后的返工清单（2026-10-13 体检结果）

> 好消息：**5 张立绘是同一个人、同一套光、同一间屋子；3 张背景风格统一** —— 最难的部分一次过了。
> 下面是需要处理的项，按优先级排。

### 必须返工

**① `officer_impatient.jpg` 分辨率只有一半**
其他四张是 2752×1536，只有它是 1376×768（放大到 1080p 会明显发糊）。请用和另外四张**完全相同的尺寸**重出这一张。

**② UI 图必须导出 PNG + 保留透明通道**
现在六张 UI 都是 JPEG，**把"透明棋盘格"当成真实像素烧进图里了**（一格格的灰白方块）。我已经用图像处理救回六张
（见 `assets/ui/*.png`，工具是 `tools/dechecker.py`），但下一批请直接：
在导出面板选 **PNG、保留 alpha**。如果工具只能导出 JPEG，就先告诉我，我用工具处理。
另外第 4 个按钮（禁用态）在抠图时被吃掉了 —— 这个状态**不用再出图**，我会用引擎做去饱和 + 半透明。

**③ `item_bank_statement_clean.jpg` 与 `item_bank_statement.jpg` 不是"同一份文件"**
叙事上它们是**同一份银行流水的「原版」和「整理版」**（玩家在解谜里把脏版修补成净版），
但现在两张是两家不同的银行、两套不同的日期版式（一个 2026 年 + 黄色荧光笔，一个 2018/2019 年）。
请**以 `item_bank_statement.jpg` 作参考图**重出整理版：同一版式、同一批日期与金额，去掉黄色荧光笔、
纸张熨平、光线更干净。玩家要能一眼看出"这是同一张纸，被收拾过了"。

### 建议修改

**④ `officer_interested` 与 `officer_caught` 太像**（都是嘴角上扬）
这两张一个是奖励、一个是惩罚，必须一眼分辨：
- `interested`：眉毛抬起 + 眼睛睁大 + 嘴唇微张（"被勾起了兴趣"）
- `caught`：单边冷笑 + 眼睛眯起 + 下巴微抬（"我看穿你了"）

**⑤ 纸面文字**
卡片小窗里看不清无所谓，但**材料详情弹窗会放大到 1080×720**，现在能读到 `lorem ipsum`、
`COMPANY LETHHEA`、`Dear Teste of Employment` 这类乱码。下一批请在负面词里加
`gibberish text, lorem ipsum, misspelled words`，或直接要求纸面文字为 `illegible blurred print`。

**⑥ `item_hotel_booking` 上的 "Booking Company" 标识**接近真实商标，
换成虚构抬头（`HOTEL METROPOLIS` 自己的 logo）即可。

### 确认通过，不用动

- 5 张立绘的人物一致性、光线、构图（背景差异实测只有 2.4–3.9/255，切表情时画面不会跳）
- 3 张背景，风格与立绘里的房间一致
- 图章、对话框、计量条抠出来后很干净
- 护照 / 邀请函 / 在职证明 / 酒店单的整体质感

### 待你拍板：立绘要不要透明底

立绘的背景已经烧进图里，没有透明通道。两条路：

| 方案 | 做法 | 代价 |
|---|---|---|
| **A（推荐）** | 接受"**整幅场景图**"：每张表情就是完整一屏，切换时背景几乎不动；`room_interview.jpg` 正好当"签证官不在"的镜头 | **零返工**，马上能进 Ren'Py |
| B | 重出透明底立绘：prompt 加 `isolated on a pure white background, no environment, no room`，再抠图 | 多一轮返工，之后可自由摆位/缩放 |
