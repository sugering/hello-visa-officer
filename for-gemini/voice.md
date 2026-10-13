# 配音提示词包（给 TTS 或配音员）

> 台本已经自动导出：`voice-lines.csv`（7 句 / 115 字，改台词后重跑 `prototype/export_voice_lines.py` 即可更新）。
> 本文件负责"怎么念"。

## 0. 先说实话：这一关有多便宜

| 方案 | 单价 | P0（7 句 / 115 字） | 全量 8 关（约 60 句） |
|---|---|---|---|
| TTS 生成 | 免费 | ¥0 | ¥0 |
| 业余配音 / 学生 | ¥5–15 / 句 | ¥35–100 | ¥300–900 |
| 专业棚录 | ¥30–80 / 句 | ¥200–500 | **¥2000–5000** |

我上次说的"四位数"是按**专业棚录全量**估的。P0 只有 7 句，其实很便宜。

**推荐策略**：TTS 打底跑通全流程 → 试玩后只重录 3 句关键台词（`greeting` / `q_funds_probe` / `verdict`）。
玩家对"开场、被抓住、裁决"三处的语气最敏感，中间那些例行提问用 TTS 完全够。

## 1. 声音设定卡（给配音员看的，也可作 TTS 的 system 描述）

- 性别 / 年龄感：男，40 岁上下（不要"青年音"，也不要"爷爷音"）
- 音区：中低音，胸腔共鸣为主，不飙高音
- 语速：偏慢，句子之间敢留白；这是权力感的来源
- 底色：**冷静、克制、公事公办**。不温柔、不油腻、不播音腔
- 口音：中性普通话，不带明显方言或儿化
- 细节：气声少，尾音收得干脆，疑问句**不上扬**（上扬会变成"讨好"，方向就反了）
- 禁忌：不要"磁性磁性"的广告腔，不要突然加重情绪 —— 他越平，玩家越慌

## 2. TTS 提示词模板（英文，通用）

先把这段**voice 描述**固定下来，之后每句只换最后一行：

```
Voice: adult male, early 40s, low-to-mid register, calm and controlled, minimal breathiness, unhurried pace.
Delivery: official and impersonal, as if reading the 37th identical case of the day. Dry, close-mic'd, no smile in the voice.
Consonants crisp, falling intonation at the ends of questions. Do not perform emotion; keep it flat and watchful.
Language: Mandarin Chinese.
Output only the spoken line. Do not add any introduction, translation, or commentary.
Line:
```

然后按台本逐句追加情绪指令（来自 `voice-lines.csv` 的 emotion 列）：

| line_id | 追加一行 |
|---|---|
| `greeting` | `Almost bored. Slight emphasis on the last two words.` |
| `q_purpose` | `Flat and routine. No rise at the end.` |
| `q_purpose_probe` | `Quietly skeptical. Half-beat pause between the two missing items.` |
| `q_funds` | `Slow and level. Let the silence after the question sit.` |
| `q_funds_probe` | `Impatient but never raised. Articulate each number distinctly.` |
| `q_ties` | `Tired, routine. Weight on the word meaning "must".` |
| `verdict` | `Completely flat. This is a formality, not a decision announcement.` |

## 3. 试音稿（挑音色 / 找配音员就用这 3 句）

覆盖三种情绪，最能听出功力的组合：

1. **例行** —— `去美国做什么？`
2. **施压（最关键）** —— `流水显示这笔钱是上周分三笔现金存入的，之前余额几乎为零。`
3. **留白** —— `在这里等一下。`

判断标准：第 2 句**没有提高音量**却让人后背发凉 → 对味；第 1 句读得礼貌客气 → 不对，他不是服务业。

## 4. 交付规范

| 项 | 要求 |
|---|---|
| 格式 | WAV，48 kHz / 24 bit，单声道 |
| 电平 | 峰值 -3 dB，整体约 -16 LUFS |
| 头尾 | 前后各留 150–250 ms 静音（方便引擎对齐，别裁干净） |
| 降噪 | 轻降噪即可，**不要**做到塑料感；房间混响要短 |
| 分轨 | 人声单独一轨，不含任何音乐或音效 |
| 命名 | `officer_<line_id>.wav`，例如 `officer_q_funds_probe.wav` |
| 存放 | `assets/audio/voice/` |

## 5. 录音顺序与常见坑

- 顺序：先录 `verdict` 和 `q_purpose` 这种短的校准状态，再录长的。
- 一次录 3 遍，选最平的那条 —— 配音员容易"演过头"，而这个角色的力量恰恰来自不演。
- 坑：句尾吞音；「几乎为零」的零读成儿化；两句之间连读（必须一句一个文件）。
- 每句录完**静默 2 秒**再录下一句，方便后期切分。

## 6. 如果你想让 Gemini 那边直接做

Gemini 应用里可以直接朗读中文，AI Studio 网页版也有语音生成；
若要更可控，ElevenLabs 免费额度或国内 TTS（MiniMax / 讯飞）都能用上面的模板。

**要不要我用免费 TTS 给你先生成一版全量占位音？** 说一声我就装依赖跑（这一步需要联网安装，可能要你批准一次）。
