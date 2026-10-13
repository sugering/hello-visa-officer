# BGM 与音效提示词

> 这部分**不建议花钱**：BGM 用 AI 生成或免费曲库，音效直接用免费素材库。
> 下面是可以直接复制进 Suno / Udio / Stable Audio 的提示词。

## 1. BGM（4 首，循环用）

### 等候区 —— 轻微不安
```
Instrumental only, no vocals, loopable. Minimal tense ambient underscore for a visa waiting room.
Low sustained string drone, sparse single piano notes with long decay, a slow heartbeat-like sub pulse,
no melodic hook, no drums, no build. Cold, patient, slightly oppressive. 85 BPM. Seamless loop, 90 seconds.
```

### 面试常规 —— 克制紧张（P0 必须有）
```
Instrumental only, no vocals, loopable. Restrained tension underscore for a face-to-face interrogation.
Muted staccato string ostinato, a dry clock-like percussive pulse, low cello pedal tone, minor key,
no melody on top, no climax, documentary-like and cold. 100 BPM. Seamless loop, 120 seconds.
```

### 解谜 —— 专注、轻快（与面试形成反差）
```
Instrumental only, no vocals, loopable. Light puzzle-solving music, playful but restrained.
Pizzicato strings, marimba, soft brushed drums, a simple repeating motif in a major key,
clean and clockwork-like, never silly. 110 BPM. Seamless loop, 90 seconds.
```

### 结局 —— 悬停 → 落定
```
Instrumental only, no vocals. Two 15-second stingers sharing the same opening:
a suspended unresolved chord held for eight seconds, then resolving either
(A) warm and open in a major key — approval, or
(B) cold and hollow in a minor key — denial. No drums, no vocals. 30 seconds total.
```

## 2. 音效（12 个，直接找免费素材，不生成）

在 freesound.org / Pixabay 搜英文关键词命中率最高：

| 用途 | 搜索关键词 |
|---|---|
| 纸张翻动 ×2 | `paper flip`、`page turn close` |
| 材料放到桌上 | `paper slide on desk`、`document placed` |
| 盖章（通过 / 拒签） | `rubber stamp thud`、`stamp impact` |
| 时钟滴答（随回合加快） | `clock tick loop`、`ticking clock` |
| UI 点击 / 悬停 / 返回 | `ui click`、`ui hover soft`、`ui back` |
| 怀疑度上升 | `low whoosh tension`、`riser short` |
| 心跳（怀疑度 ≥ 70 循环） | `heartbeat loop`、`heartbeat slow` |
| 解谜成功 / 失败 | `puzzle solved chime`、`error buzz soft` |

要求：全部转成 **OGG Vorbis**（Ren'Py 推荐格式），命名对齐 `assets/audio/sfx/`，例如 `sfx_stamp_approved.ogg`。

## 3. 如果一定要 AI 生成音效

Stable Audio / ElevenLabs SFX 可用这类短提示：

```
A single rubber stamp hitting a wooden desk, close perspective, dry thud with a short paper rustle tail, no reverb, 1 second.
```

```
An old mechanical clock ticking in a quiet room, slow and regular, close-miked, no music, loopable, 4 seconds.
```
