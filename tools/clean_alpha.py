"""在 dechecker 的输出上做连通域清理：只保留成规模的主体，去掉散落残留。

棋盘格在 JPEG 里深浅不均，色键只能抠掉大部分，剩下的小块残留用"连通域太小就丢弃"清掉。
纯 numpy 实现（8 倍下采样后做 BFS 连通域），不依赖 scipy。
"""

from __future__ import annotations

from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
UI = ROOT / "assets" / "ui"
SCALE = 8
MIN_AREA = 20          # 下采样后的格子数
MIN_KEEP_RATIO = 0.02  # 保住最大的连通域，避免整张被清空


def largest_components(mask: np.ndarray) -> np.ndarray:
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    keep = np.zeros_like(mask, dtype=bool)
    areas = []
    comps = []
    for sy in range(h):
        for sx in range(w):
            if not mask[sy, sx] or seen[sy, sx]:
                continue
            q = deque([(sy, sx)])
            seen[sy, sx] = True
            cells = []
            while q:
                y, x = q.popleft()
                cells.append((y, x))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        q.append((ny, nx))
            areas.append(len(cells))
            comps.append(cells)
    if not areas:
        return keep
    cutoff = max(MIN_AREA, int(max(areas) * MIN_KEEP_RATIO))
    for area, cells in zip(areas, comps):
        if area >= cutoff:
            for y, x in cells:
                keep[y, x] = True
    return keep


def main() -> None:
    for p in sorted(UI.glob("*.png")):
        if p.name.startswith("_"):
            continue
        im = Image.open(p).convert("RGBA")
        alpha = np.asarray(im.getchannel("A"))
        h, w = alpha.shape
        h2, w2 = h // SCALE, w // SCALE
        small = (alpha[: h2 * SCALE, : w2 * SCALE] > 100).reshape(h2, SCALE, w2, SCALE).max(axis=(1, 3))
        keep_small = largest_components(small)
        keep = np.repeat(np.repeat(keep_small, SCALE, axis=0), SCALE, axis=1)
        full = np.zeros_like(alpha, dtype=bool)
        full[: h2 * SCALE, : w2 * SCALE] = keep
        new_alpha = (alpha * full).astype(np.uint8)
        out = im.copy()
        out.putalpha(Image.fromarray(new_alpha, "L"))
        out.save(p)
        print(f"{p.name:<28}残留像素 {1 - (alpha > 100).mean():.1%} → {1 - (new_alpha > 100).mean():.1%}")


if __name__ == "__main__":
    main()
