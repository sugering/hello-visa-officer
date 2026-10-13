"""从 content/dialogue.json 导出配音台本（CSV）。

台词的语气提示就写在 dialogue.json 每个节点的 "voice" 字段里 ——
内容和语气放在一起，改台词的人顺手就能改语气；这个脚本只负责导出，不做任何判断。

运行： python export_voice_lines.py
产出： ../for-gemini/voice-lines.csv（UTF-8 BOM，Excel 直接双击可开）
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DIALOGUE = HERE / "content" / "dialogue.json"
OUT = HERE.parent / "for-gemini" / "voice-lines.csv"

FIELDS = ["line_id", "text", "emotion", "pace", "note", "chars"]


def collect() -> list:
    data = json.loads(DIALOGUE.read_text(encoding="utf-8"))
    rows = []
    for node_id, node in data["nodes"].items():
        if node.get("speaker", "officer") != "officer" or not node.get("text"):
            continue
        voice = node.get("voice", {})
        rows.append({
            "line_id": node_id,
            "text": node["text"],
            "emotion": voice.get("emotion", ""),
            "pace": voice.get("pace", ""),
            "note": voice.get("note", ""),
            "chars": len(node["text"]),
        })
    return rows


def main() -> None:
    rows = collect()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"导出 {len(rows)} 句 / 共 {sum(r['chars'] for r in rows)} 字 -> {OUT}")


if __name__ == "__main__":
    main()
