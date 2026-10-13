"""demo 的视觉常量：资产路径、裁切区域、配色、字体、版面尺寸。

所有数值都来自对 assets/ 里真实图片的测量（见 tools/ 与预览图），不是拍脑袋写的。
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageFont

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

SCREEN = (1920, 1080)

# ---- 配色 ----------------------------------------------------------------
INK = (232, 230, 225)
INK_DIM = (150, 152, 158)
ACCENT = (200, 180, 138)
WARN = (214, 138, 96)
BAD = (196, 88, 80)
GOOD = (128, 176, 128)
PANEL = (18, 20, 26, 214)
SHADE = (0, 0, 0, 150)

# ---- 字体 ----------------------------------------------------------------
# 中文字体：按平台依次找，找不到就退回 PIL 内置字体（中文会变成方块，会打印一次警告）
FONT_REG_CANDIDATES = [
    r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\msyh.ttf", r"C:\Windows\Fonts\simhei.ttf",
    "/System/Library/Fonts/PingFang.ttc", "/System/Library/Fonts/STHeiti Medium.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJKsc-Regular.otf",
]
FONT_BOLD_CANDIDATES = [
    r"C:\Windows\Fonts\msyhbd.ttc", r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simhei.ttf",
    "/System/Library/Fonts/PingFang.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
]
FONT_REG = next((p for p in FONT_REG_CANDIDATES if Path(p).exists()), None)
FONT_BOLD = next((p for p in FONT_BOLD_CANDIDATES if Path(p).exists()), FONT_REG)


@lru_cache(maxsize=32)
def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = (FONT_BOLD if bold else FONT_REG) or FONT_REG
    if path:
        return ImageFont.truetype(path, size)
    if not getattr(font, "_warned", False):
        print("警告：没找到中文字体，界面上的中文会显示成方块。"
              "Windows 装微软雅黑 / macOS 用苹方 / Linux 装 fonts-noto-cjk 即可。")
        font._warned = True
    try:
        return ImageFont.load_default(size)          # Pillow >= 10
    except TypeError:
        return ImageFont.load_default()


# ---- 版面 ----------------------------------------------------------------
DIALOGUE = (150, 580, 1620, 485)          # x, y, w, h（对话框贴底）
OPTION = {"x": 1030, "w": 790, "h": 116, "gap": 16, "top": 150}
MATERIALS = {"x": 30, "y": 96, "w": 440, "row": 56, "thumb": 48}
METER = (1150, 74, 620, 76)
PUZZLE_FRAME = (1180, 737)                # 模态框尺寸，居中
TILE = 108
TILE_GAP = 12

# 整理流水（文件整理室）：一屏 5 行，每行"槽位 + 两选一"
DESK = {"w": 1400, "h": 875, "row_h": 96, "row_gap": 6, "first_row_y": 206,
        "label_w": 290, "choice_w": 360, "choice_gap": 20, "pad": 120}
DESK_SCENE = "backgrounds/room_docs.jpg"

MOOD_FILE_EXTRA = {"desk": DESK_SCENE}

# ---- UI 元素（tools/pack_ui.py 已经按显示尺寸裁好并缩放） ------------------
UI_FILE = {
    "dialogue": "ui/dialogue.png",
    "meter": "ui/meter.png",
    "puzzle": "ui/puzzle.png",
    "button": "ui/button.png",
    "card": "ui/card.png",
    "card_submitted": "ui/card.png",
    "card_exposed": "ui/card.png",
    "stamp_approved": "ui/stamp_approved.png",
    "stamp_denied": "ui/stamp_denied.png",
    "stamp_review": "ui/stamp_review.png",
}

MOOD_FILE = {
    "calm": "characters/officer/officer_calm.jpg",
    "doubt": "characters/officer/officer_doubt.jpg",
    "impatient": "characters/officer/officer_impatient.jpg",
    "interested": "characters/officer/officer_interested.jpg",
    "caught": "characters/officer/officer_caught.jpg",
}
MOOD_LABEL = {
    "calm": "平静审视", "doubt": "轻微怀疑", "impatient": "明显不耐烦",
    "interested": "突然感兴趣", "caught": "冷笑 / 识破",
}
SOURCE_LABEL = {"genuine": "真实", "modified": "半真", "forged": "伪造"}


@lru_cache(maxsize=64)
def load(rel: str) -> Image.Image:
    return Image.open(ASSETS / rel).convert("RGBA")


@lru_cache(maxsize=16)
def ui(name: str) -> Image.Image:
    return load(UI_FILE[name])


def scene(mood: str) -> Image.Image:
    rel = MOOD_FILE.get(mood) or MOOD_FILE_EXTRA.get(mood) or MOOD_FILE["calm"]
    return load(rel).resize(SCREEN, Image.LANCZOS)


def fit(im: Image.Image, w: int, h: int) -> Image.Image:
    return im.resize((w, h), Image.LANCZOS)