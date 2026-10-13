"""把引擎状态画成一帧画面（纯 Pillow，不依赖 GUI）。

这样同一套版面既能给 tkinter 用，也能离线出预览图 —— demo 的外观可以在没有显示器的情况下验证。
"""

from __future__ import annotations

from PIL import Image, ImageDraw

from theme import (ACCENT, BAD, DESK, DIALOGUE, GOOD, INK, INK_DIM, MATERIALS, METER,
                   MOOD_LABEL, OPTION, PANEL, PUZZLE_FRAME, SCREEN, SHADE,
                   SOURCE_LABEL, TILE, TILE_GAP, WARN, fit, font, load, scene, ui)


def wrap(draw: ImageDraw.ImageDraw, text: str, f, max_w: int) -> list:
    lines, cur = [], ""
    for ch in text:
        if ch == "\n":
            lines.append(cur)
            cur = ""
            continue
        if draw.textlength(cur + ch, font=f) > max_w and cur:
            lines.append(cur)
            cur = ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines


def paste_alpha(base: Image.Image, im: Image.Image, xy) -> None:
    base.alpha_composite(im, (int(xy[0]), int(xy[1])))


def rounded(draw, box, radius, fill, outline=None, width=2):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def panel(img, d, art, box, inset, fill, radius=18):
    """贴 UI 美术底图，再把内部盖成纯色。

    美术底图内部残留着"透明棋盘格"被烧进 JPEG 的纹理（已用 tools/dechecker.py 尽量抠掉，
    但半透明区域仍有残影），盖一层纯色既干净又保证文字可读。
    """
    x, y, w, h = box
    paste_alpha(img, art, (x, y))
    rounded(d, (x + inset, y + inset, x + w - inset, y + h - inset), radius, fill)


# --------------------------------------------------------------------------
# 各区块
# --------------------------------------------------------------------------

def draw_topbar(img, d, snap):
    d.text((150, 26), f"回合 {snap['round']} / {snap['round_limit']}", font=font(34, True), fill=INK)
    d.text((150, 68), "《你好签证官》逻辑测试 Demo", font=font(22), fill=INK_DIM)

    x, y, w, h = METER
    meter = fit(ui("meter"), w, h)
    paste_alpha(img, meter, (x, y))
    ratio = min(1.0, snap["suspicion"] / max(1, snap["suspicion_limit"]))
    px = x + int(w * ratio)
    d.line([(px, y - 8), (px, y + h + 8)], fill=(255, 255, 255, 235), width=4)
    d.polygon([(px - 12, y - 10), (px + 12, y - 10), (px, y + 6)], fill=(255, 255, 255, 240))
    d.text((x, y - 46), f"怀疑度 {snap['suspicion']}  ·  立绘：{MOOD_LABEL.get(snap['mood'], snap['mood'])}",
           font=font(26, True), fill=INK)


def draw_materials(img, d, snap):
    m = MATERIALS
    owned_ids = {o["id"] for o in snap["owned"]}
    items = list(snap["owned"]) + [b for b in snap.get("submitted_detail", []) if b["id"] not in owned_ids]
    rows = len(items)
    if not rows:
        return
    h = 46 + rows * m["row"] + 10
    rounded(d, (m["x"], m["y"], m["x"] + m["w"], m["y"] + h), 14, (16, 18, 24, 200),
            outline=(90, 96, 108, 180))
    d.text((m["x"] + 16, m["y"] + 12), "材料", font=font(24, True), fill=ACCENT)
    y = m["y"] + 46
    for it in items:
        mid = it["id"]
        submitted = mid in snap["submitted"]
        exposed = mid in snap["exposed"]
        thumb = fit(load(f"items/item_{mid}.jpg"), m["thumb"], m["thumb"])
        paste_alpha(img, thumb, (m["x"] + 14, y + 2))
        d.rectangle((m["x"] + 14, y + 2, m["x"] + 14 + m["thumb"], y + 2 + m["thumb"]),
                    outline=(70, 74, 84, 200), width=1)
        name_f = font(21, True)
        d.text((m["x"] + 74, y), it["name"], font=name_f, fill=INK)
        stat = f"{SOURCE_LABEL.get(it.get('source'), it.get('source','?'))} · 可信 {it['credibility']} · 抗性 {it['robustness']}"
        d.text((m["x"] + 74, y + 26), stat, font=font(17), fill=INK_DIM)
        if exposed:
            d.text((m["x"] + m["w"] - 92, y + 12), "已击穿", font=font(19, True), fill=BAD)
        elif submitted:
            d.text((m["x"] + m["w"] - 92, y + 12), "已递交", font=font(19, True), fill=GOOD)
        y += m["row"]


def draw_dialogue(img, d, speaker, text, log_lines):
    x, y, w, h = DIALOGUE
    panel(img, d, fit(ui("dialogue"), w, h), (x, y, w, h), 66, (14, 16, 22, 238))
    pad = 64
    d.text((x + pad, y + 30), speaker, font=font(28, True), fill=ACCENT)
    body = font(32)
    ty = y + 78
    for line in wrap(d, text, body, w - pad * 2)[:3]:
        d.text((x + pad, ty), line, font=body, fill=INK)
        ty += 44
    if log_lines:
        lf = font(22)
        ly = y + h - 26 - 26 * len(log_lines[-3:])
        for line in log_lines[-3:]:
            d.text((x + pad, ly), line, font=lf, fill=INK_DIM)
            ly += 26


def draw_options(img, d, options, hover=None):
    x, w, h, gap, top = OPTION["x"], OPTION["w"], OPTION["h"], OPTION["gap"], OPTION["top"]
    art = fit(ui("button"), w, h)
    for i, opt in enumerate(options[:3]):
        y = top + i * (h + gap)
        tint = art.copy()
        if opt["locked"]:
            tint = Image.blend(tint, Image.new("RGBA", tint.size, (10, 10, 12, 255)), 0.55)
        elif hover == i:
            tint = Image.blend(tint, Image.new("RGBA", tint.size, (255, 236, 190, 255)), 0.16)
        paste_alpha(img, tint, (x, y))
        label = opt["option"].text
        warn = "  ⚠" if opt.get("conflict_preview") else ""
        d.text((x + 62, y + h // 2 - 20), label + warn,
               font=font(27, True), fill=INK if not opt["locked"] else (140, 142, 148))
        if opt["locked"]:
            d.text((x + 62, y + h // 2 + 12), opt["reason"][:34], font=font(19), fill=(206, 148, 148))


def draw_log(img, d, log_lines):
    if not log_lines:
        return
    x, y, w = 1030, 620, 790
    d.text((x, y - 30), "机制日志", font=font(20, True), fill=INK_DIM)
    lf = font(21)
    yy = y
    for line in log_lines[-8:]:
        d.text((x, yy), line, font=lf, fill=INK_DIM)
        yy += 27


# --------------------------------------------------------------------------
# 谜题
# --------------------------------------------------------------------------

def draw_puzzle(img, d, board, flavor, moves, budget, hover=None):
    img.alpha_composite(Image.new("RGBA", SCREEN, SHADE))
    fw, fh = PUZZLE_FRAME
    frame = fit(ui("puzzle"), fw, fh)
    fx, fy = (SCREEN[0] - fw) // 2, (SCREEN[1] - fh) // 2
    panel(img, d, frame, (fx, fy, fw, fh), 86, (20, 22, 28, 242))
    d.text((fx + 90, fy + 62), "对齐印章", font=font(38, True), fill=INK)
    d.text((fx + 90, fy + 116), flavor, font=font(24), fill=INK_DIM)

    n = board.size
    gw = n * TILE + (n - 1) * TILE_GAP
    gx = fx + (fw - gw) // 2
    gy = fy + 200
    for r in range(n):
        for c in range(n):
            i = r * n + c
            bx = gx + c * (TILE + TILE_GAP)
            by = gy + r * (TILE + TILE_GAP)
            on = bool(board.cells[i])
            base = (86, 96, 108, 255) if on else (30, 34, 42, 255)
            edge = (210, 200, 170, 255) if (hover == i) else (120, 128, 140, 255)
            rounded(d, (bx, by, bx + TILE, by + TILE), 14, base, outline=edge, width=3)
            d.text((bx + TILE // 2 - 14, by + TILE // 2 - 20),
                   "●" if on else "·", font=font(34, True), fill=(250, 240, 210) if on else (90, 96, 106))
    d.text((gx, gy + gw + 26), f"步数 {moves} / 预算 {budget}　（点击格子，会同时翻转上下左右）",
           font=font(24), fill=INK)
    rounded(d, (fx + fw - 260, fy + fh - 96, fx + fw - 90, fy + fh - 36), 12, (40, 44, 54, 255),
            outline=(120, 128, 140, 220))
    d.text((fx + fw - 224, fy + fh - 84), "放弃", font=font(26, True), fill=INK)


# --------------------------------------------------------------------------
# 整理流水（文件整理室）
# --------------------------------------------------------------------------

def desk_geometry(n_slots: int):
    """整理台的版面几何。session 也用它做命中测试，避免两处各写一遍坐标。"""
    fw, fh = DESK["w"], DESK["h"]
    fx, fy = (SCREEN[0] - fw) // 2, (SCREEN[1] - fh) // 2
    rows = []
    for i in range(n_slots):
        y = fy + DESK["first_row_y"] + i * (DESK["row_h"] + DESK["row_gap"])
        lx = fx + DESK["pad"]
        ax = lx + DESK["label_w"] + DESK["choice_gap"]
        bx = ax + DESK["choice_w"] + DESK["choice_gap"]
        rows.append({"label": (lx, y, DESK["label_w"], DESK["row_h"]),
                     "safe": (ax, y, DESK["choice_w"], DESK["row_h"]),
                     "bold": (bx, y, DESK["choice_w"], DESK["row_h"])})
    by = fy + fh - 161                      # 底部操作区留出边框的空档
    submit = (fx + fw - DESK["pad"] - 300, by, 300, 58)
    skip = (submit[0] - 336, by, 316, 58)
    return (fx, fy, fw, fh), rows, submit, skip


def draw_choice(d, rect, choice, selected, hover):
    x, y, w, h = rect
    fill = (54, 60, 74, 255) if selected else (30, 34, 42, 236)
    edge = ACCENT if selected else ((150, 156, 168, 255) if hover else (96, 102, 114, 220))
    rounded(d, (x, y, x + w, y + h), 12, fill, outline=edge, width=3 if selected else 2)
    d.text((x + 20, y + 12), choice["label"], font=font(22, True),
           fill=INK if selected else (214, 214, 210))
    d.text((x + 20, y + 42), choice["detail"], font=font(17), fill=INK_DIM)
    d.text((x + w - 72, y + 12), f"+{choice['credibility']}", font=font(22, True),
           fill=GOOD if selected else (150, 178, 150))
    if choice.get("flaw"):
        d.text((x + 20, y + 66), "破绽：" + choice["flaw"], font=font(17), fill=BAD)
    if selected:
        # 用 √（U+221A）而不是 ✓（U+2713）：微软雅黑没有后者，会渲染成方框
        d.text((x + w - 44, y + 40), "√", font=font(32, True), fill=ACCENT)


def draw_desk(img, d, board, cfg, hover=None):
    panel(img, d, fit(ui("puzzle"), DESK["w"], DESK["h"]),
          ((SCREEN[0] - DESK["w"]) // 2, (SCREEN[1] - DESK["h"]) // 2, DESK["w"], DESK["h"]),
          86, (22, 20, 24, 240))
    (fx, fy, fw, fh), rows, submit, skip = desk_geometry(len(board.slots))
    d.text((fx + DESK["pad"], fy + 100), cfg["name"], font=font(36, True), fill=INK)
    for i, line in enumerate(wrap(d, cfg["flavor"], font(21), fw - DESK["pad"] * 2)[:2]):
        d.text((fx + DESK["pad"], fy + 148 + 28 * i), line, font=font(21), fill=INK_DIM)

    for slot, rect in zip(board.slots, rows):
        lx, ly, lw, lh = rect["label"]
        d.text((lx, ly + 16), slot["label"], font=font(23, True), fill=INK)
        d.text((lx, ly + 52), "这一行怎么处理？", font=font(18), fill=INK_DIM)
        for which in ("safe", "bold"):
            chosen = board.picks.get(slot["id"]) == which
            draw_choice(d, rect[which], slot[which], chosen, hover == (slot["id"], which))

    flaws = board.flaws()
    by = fy + fh - 161
    d.text((fx + DESK["pad"], by + 2),
           f"可信度 {board.credibility()}　抗性 {board.robustness()}　破绽 {len(flaws)}",
           font=font(26, True), fill=INK)
    if flaws:
        d.text((fx + DESK["pad"], by + 36), "　".join(flaws)[:56], font=font(18), fill=BAD)
    else:
        d.text((fx + DESK["pad"], by + 36), "干干净净，但分数也低", font=font(18), fill=INK_DIM)

    kx, ky, kw, kh = skip
    rounded(d, (kx, ky, kx + kw, ky + kh), 12, (30, 34, 42, 236), outline=(110, 112, 120, 210))
    d.text((kx + 26, ky + 18), "原样交上去（不整理）", font=font(20, True), fill=(196, 196, 200))

    sx, sy, sw, sh = submit
    ready = board.is_solved()
    rounded(d, (sx, sy, sx + sw, sy + sh), 12,
            (54, 62, 76, 255) if ready else (32, 36, 44, 220),
            outline=ACCENT if ready else (90, 96, 108, 200), width=3 if ready else 2)
    d.text((sx + 40, sy + 12), "就这样交上去" if ready else "还有没处理的",
           font=font(24, True), fill=INK if ready else (140, 144, 150))


# --------------------------------------------------------------------------
# 结局
# --------------------------------------------------------------------------

ENDING = {
    "approved": ("stamp_approved", "通过", GOOD),
    "administrative_review": ("stamp_review", "行政审查 221(g)", WARN),
    "denied": ("stamp_denied", "拒签", BAD),
    "caught": ("stamp_denied", "当场识破", BAD),
}


def draw_ending(img, d, verdict):
    img.alpha_composite(Image.new("RGBA", SCREEN, (0, 0, 0, 178)))
    key, label, color = ENDING.get(verdict["ending"], ENDING["denied"])
    stamp = ui(key)
    stamp = fit(stamp, 460, int(460 * stamp.height / stamp.width))
    px = (SCREEN[0] - stamp.width) // 2
    paste_alpha(img, stamp, (px, 150))

    x, y, w, h = 420, 500, 1080, 400
    rounded(d, (x, y, x + w, y + h), 18, PANEL, outline=(100, 106, 118, 220))
    d.text((x + 48, y + 34), f"结局：{label}", font=font(40, True), fill=color)
    lines = [
        f"总分 {verdict['score']}　=　覆盖率 {verdict['coverage']} × 70　+　材料质量 {verdict['quality']} × 30",
        f"　　　　　　　+　修正 {verdict['bonus']:+d}　−　怀疑度 {verdict['suspicion']} × 0.3",
        f"覆盖情况：" + "、".join(f"{k} {v}" for k, v in verdict["covered"].items()),
        f"缺项：{'、'.join(verdict['missing']) or '无'}",
        f"说漏嘴（陈述与材料矛盾）：{'是' if verdict['caught_lying'] else '否'}　·　"
        f"回国约束材料：{'有' if verdict['ties_ok'] else '无'}　·　触发：{verdict['reason']}",
        "按 R 重新开始，按 Esc 退出",
    ]
    ty = y + 108
    for line in lines:
        for seg in wrap(d, line, font(24), w - 96):
            d.text((x + 48, ty), seg, font=font(24), fill=INK)
            ty += 34
        ty += 6


# --------------------------------------------------------------------------
# 主入口
# --------------------------------------------------------------------------

def render(*, mood="calm", speaker="签证官", text="", options=(), snapshot=None,
           log_lines=(), mode="interview", board=None, puzzle=None, ending=None,
           hover_option=None, hover_cell=None, hover_desk=None) -> Image.Image:
    img = scene("desk" if mode == "desk" else mood).copy()
    d = ImageDraw.Draw(img, "RGBA")
    draw_topbar(img, d, snapshot)
    if mode != "desk":                 # 整理台用满屏，材料面板会挡住单子
        draw_materials(img, d, snapshot)

    if mode == "desk" and board is not None:
        draw_desk(img, d, board, puzzle, hover_desk)
    elif mode == "puzzle" and board is not None:
        draw_puzzle(img, d, board, puzzle["flavor"], board.move_count, puzzle["move_budget"], hover_cell)
    elif mode == "ending" and ending is not None:
        draw_ending(img, d, ending)
    else:
        if options:
            draw_options(img, d, options, hover_option)
        draw_dialogue(img, d, speaker, text, log_lines)
    return img
