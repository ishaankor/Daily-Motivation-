"""Graphics rendering engine for daily framework cards optimized for high dwell time and bookmarks."""

import os
import time
from typing import Dict, Any, Optional, List
from PIL import Image, ImageDraw, ImageFont

from bot.config import paths, twitter_config

# Day of week names
DAY_NAMES = {
    0: "MOTIVATION MONDAY",
    1: "STOIC TUESDAY",
    2: "WISDOM WEDNESDAY",
    3: "TENACITY THURSDAY",
    4: "FOCUS FRIDAY",
    5: "SUCCESS SATURDAY",
    6: "SUNDAY RESET"
}

# Style mapping (Obsidian Luxury Framework Card is the flagship standard)
WEEKDAY_STYLES = {
    0: "obsidian",
    1: "obsidian",
    2: "obsidian",
    3: "obsidian",
    4: "obsidian",
    5: "obsidian",
    6: "obsidian"
}


def get_font(font_names: List[str], size: int) -> ImageFont.ImageFont:
    """Load font from assets/fonts first, then search system paths, with fallback."""
    # 1. Check local assets/fonts directory
    font_dir = os.path.join(paths.base_dir, "assets", "fonts")
    if os.path.exists(font_dir):
        for name in font_names:
            local_path = os.path.join(font_dir, name)
            if os.path.exists(local_path):
                try:
                    return ImageFont.truetype(local_path, size)
                except Exception:
                    pass

    # 2. Check system font directories
    system_dirs = [
        "/System/Library/Fonts/Supplemental",
        "/System/Library/Fonts",
        "/Library/Fonts",
        "/usr/share/fonts",
        "/usr/share/fonts/truetype",
        "/usr/share/fonts/truetype/dejavu",
        "/usr/share/fonts/truetype/liberation",
        "C:\\Windows\\Fonts"
    ]
    for name in font_names:
        for sdir in system_dirs:
            full = os.path.join(sdir, name)
            if os.path.exists(full):
                try:
                    return ImageFont.truetype(full, size)
                except Exception:
                    pass

    return ImageFont.load_default()


def wrap_text(text: str, font: ImageFont.ImageFont, max_width: int, draw: ImageDraw.Draw) -> List[str]:
    """Word wrap text to fit within max_width."""
    words = text.split(" ")
    lines = []
    current_line = []
    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if (bbox[2] - bbox[0]) <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))
    return lines


def render_obsidian_framework_card(
    entry: Dict[str, Any],
    output_path: Optional[str] = None,
    width: int = 1080,
    height: int = 1350
) -> str:
    """
    Render the Obsidian Luxury Framework Card.
    Engineered for maximum dwell time, bookmark rate, and authority on X.
    """
    if not output_path:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(paths.output_dir, f"obsidian_card_{timestamp}.png")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # 1. Base Dark Canvas
    base = Image.new("RGBA", (width, height), (13, 14, 18, 255))

    # 2. Ambient Gold Halo at top
    halo = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    hdraw = ImageDraw.Draw(halo)
    for r in range(420, 0, -6):
        alpha = int((1 - (r / 420)) * 52)
        hdraw.ellipse([width // 2 - r * 2, -r - 50, width // 2 + r * 2, r * 2], fill=(212, 175, 55, alpha))
    base = Image.alpha_composite(base, halo)
    draw = ImageDraw.Draw(base)

    # 3. Outer Double Border & 24K Gold Corner Pins
    m = 48
    draw.rectangle([m, m, width - m, height - m], outline=(55, 58, 68, 200), width=1)
    draw.rectangle([m + 10, m + 10, width - m - 10, height - m - 10], outline=(180, 150, 80, 120), width=1)
    for cx, cy in [
        (m + 10, m + 10),
        (width - m - 10, m + 10),
        (m + 10, height - m - 10),
        (width - m - 10, height - m - 10)
    ]:
        draw.rectangle([cx - 3, cy - 3, cx + 3, cy + 3], fill=(212, 175, 55, 240))

    primary_gold = (212, 175, 55)
    light_gold = (230, 205, 125)

    # 4. Typography Loading
    font_badge = get_font(["Inter.ttf", "Avenir Next.ttc", "HelveticaNeue.ttc"], 18)
    font_quote = get_font(["PlayfairDisplay.ttf", "Georgia Bold.ttf", "Charter.ttc"], 46)
    font_author = get_font(["PlayfairDisplay-Italic.ttf", "Lora-Italic.ttf", "Georgia Italic.ttf"], 26)
    font_section_hdr = get_font(["Inter.ttf", "Avenir Next Condensed.ttc"], 21)
    font_num = get_font(["Inter.ttf", "Avenir Next.ttc"], 20)
    font_body = get_font(["Inter.ttf", "HelveticaNeue.ttc"], 23)
    font_axiom_title = get_font(["Inter.ttf", "Avenir Next.ttc"], 19)
    font_axiom = get_font(["Lora-Italic.ttf", "PlayfairDisplay-Italic.ttf", "Georgia.ttf"], 26)
    font_footer = get_font(["Inter.ttf", "Avenir.ttc"], 18)

    # 5. Top Pill Eyebrow Badge
    theme_title = entry.get("theme") or DAY_NAMES.get(time.localtime().tm_wday, "DAILY MINDSET")
    category = entry.get("category", "EXECUTION").upper()
    badge_text = f"•  {theme_title.upper()}  •  {category}  •"
    bbox = draw.textbbox((0, 0), badge_text, font=font_badge)
    bw, bh = bbox[2] - bbox[0], bbox[3] - bbox[1]
    bx, by = width // 2, m + 68
    draw.rounded_rectangle(
        [bx - bw // 2 - 26, by - bh // 2 - 9, bx + bw // 2 + 26, by + bh // 2 + 9],
        radius=16,
        fill=(22, 23, 30, 230),
        outline=(primary_gold[0], primary_gold[1], primary_gold[2], 180),
        width=1
    )
    draw.text((bx - bw // 2, by - bh // 2 - 2), badge_text, font=font_badge, fill=light_gold + (255,))

    # 6. Hero Quote Section
    quote_clean = f"“{entry.get('quote', '').strip('\"')}”"
    q_lines = wrap_text(quote_clean, font_quote, width - 220, draw)
    line_h = 64
    q_y = by + 65
    for line in q_lines:
        l_bbox = draw.textbbox((0, 0), line, font=font_quote)
        lx = (width - (l_bbox[2] - l_bbox[0])) // 2
        draw.text((lx, q_y), line, font=font_quote, fill=(255, 255, 255, 255))
        q_y += line_h

    # 7. Author Line
    q_y += 14
    auth_text = f"—  {entry.get('author', '').strip()}  —"
    a_bbox = draw.textbbox((0, 0), auth_text, font=font_author)
    draw.text(((width - (a_bbox[2] - a_bbox[0])) // 2, q_y), auth_text, font=font_author, fill=primary_gold + (240,))
    q_y += 38
    draw.line([(width // 2 - 70, q_y), (width // 2 + 70, q_y)], fill=(primary_gold[0], primary_gold[1], primary_gold[2], 90), width=1)

    # 8. Middle Framework Container (3 Tactical Principles)
    box_top = q_y + 45
    box_w = width - 160
    box_h = 470
    box_x = 80

    f_card = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    f_draw = ImageDraw.Draw(f_card)
    f_draw.rounded_rectangle(
        [box_x, box_top, box_x + box_w, box_top + box_h],
        radius=22,
        fill=(20, 22, 28, 220),
        outline=(55, 60, 75, 220),
        width=1
    )
    base = Image.alpha_composite(base, f_card)
    draw = ImageDraw.Draw(base)

    is_sunday = "SUNDAY" in theme_title.upper()
    hdr_text = "WEEKLY REALIGNMENT PRINCIPLES" if is_sunday else "TACTICAL EXECUTION PRINCIPLES"
    draw.text((box_x + 35, box_top + 28), hdr_text, font=font_section_hdr, fill=primary_gold + (250,))
    draw.line([(box_x + 35, box_top + 64), (box_x + box_w - 35, box_top + 64)], fill=(48, 52, 65, 255), width=1)

    takeaways = entry.get("takeaways", [
        "Persist relentlessly through friction without forfeiting momentum.",
        "Reframe unforeseen obstacles into high-leverage stepping stones.",
        "Unforgiving compound effort consistently dismantles fleeting luck."
    ])

    row_y = box_top + 86
    row_h = 104
    row_spacing = 20

    for i, item in enumerate(takeaways[:3]):
        ry = row_y + i * (row_h + row_spacing)
        rx = box_x + 25
        rw = box_w - 50

        draw.rounded_rectangle([rx, ry, rx + rw, ry + row_h], radius=14, fill=(15, 16, 21, 230), outline=(45, 48, 60, 210), width=1)

        # Number pill badge
        num_str = f"0{i+1}"
        num_w, num_h = 50, 50
        nx = rx + 22
        ny = ry + (row_h - num_h) // 2
        draw.rounded_rectangle(
            [nx, ny, nx + num_w, ny + num_h],
            radius=11,
            fill=primary_gold + (30,),
            outline=primary_gold + (190,),
            width=1
        )
        n_bbox = draw.textbbox((0, 0), num_str, font=font_num)
        nw, nh = n_bbox[2] - n_bbox[0], n_bbox[3] - n_bbox[1]
        draw.text((nx + (num_w - nw) // 2, ny + (num_h - nh) // 2 - 1), num_str, font=font_num, fill=light_gold + (255,))

        # Text
        t_lines = wrap_text(item, font_body, rw - 115, draw)
        ty = ry + (row_h - (len(t_lines) * 32)) // 2
        for tl in t_lines:
            draw.text((rx + 92, ty), tl, font=font_body, fill=(238, 240, 246, 255))
            ty += 32

    # 9. Core Law / Axiom Container
    axiom = entry.get("axiom")
    if not axiom:
        axiom = entry.get("prompt") or (takeaways[0] if takeaways else "Effort is the singular variable 100% within your command.")

    ax_top = box_top + box_h + 38
    ax_h = 145
    ax_card = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    ax_draw = ImageDraw.Draw(ax_card)
    ax_draw.rounded_rectangle(
        [box_x, ax_top, box_x + box_w, ax_top + ax_h],
        radius=20,
        fill=(24, 21, 15, 220),
        outline=primary_gold + (180,),
        width=1
    )
    base = Image.alpha_composite(base, ax_card)
    draw = ImageDraw.Draw(base)

    # Axiom Label Pill
    ax_tag = "WEEKLY AXIOM" if is_sunday else "CORE LAW"
    at_bbox = draw.textbbox((0, 0), ax_tag, font=font_axiom_title)
    at_w, at_h = at_bbox[2] - at_bbox[0], at_bbox[3] - at_bbox[1]
    draw.rounded_rectangle(
        [width // 2 - at_w // 2 - 16, ax_top - 14, width // 2 + at_w // 2 + 16, ax_top + 14],
        radius=7,
        fill=(18, 19, 25, 255),
        outline=primary_gold + (210,),
        width=1
    )
    draw.text((width // 2 - at_w // 2, ax_top - at_h // 2 - 2), ax_tag, font=font_axiom_title, fill=primary_gold + (255,))

    # Axiom Text
    ax_clean = f"“{axiom.strip('\"')}”"
    ax_lines = wrap_text(ax_clean, font_axiom, box_w - 70, draw)
    ax_txt_y = ax_top + 42
    for al in ax_lines:
        al_bbox = draw.textbbox((0, 0), al, font=font_axiom)
        al_x = (width - (al_bbox[2] - al_bbox[0])) // 2
        draw.text((al_x, ax_txt_y), al, font=font_axiom, fill=(255, 240, 195, 255))
        ax_txt_y += 36

    # 10. Algorithmic Retention Cue Ribbon (Vector Bookmark)
    cue_top = ax_top + ax_h + 40
    cue_text = "BOOKMARK FOR SUNDAY AUDIT" if is_sunday else "BOOKMARK TO REVISIT"
    ribbon_w = 380 if is_sunday else 340
    ribbon_h = 36
    rx_c = width // 2 - ribbon_w // 2
    draw.rounded_rectangle([rx_c, cue_top, rx_c + ribbon_w, cue_top + ribbon_h], radius=18, fill=(22, 24, 32, 200), outline=(50, 54, 66, 180), width=1)

    bm_x = rx_c + 20
    bm_y = cue_top + 9
    bm_pts = [(bm_x, bm_y), (bm_x + 12, bm_y), (bm_x + 12, bm_y + 18), (bm_x + 6, bm_y + 13), (bm_x, bm_y + 18)]
    draw.polygon(bm_pts, fill=primary_gold + (240,))

    draw.text((bm_x + 22, cue_top + 8), cue_text, font=font_footer, fill=(190, 195, 210, 255))

    # 11. Bottom Signature & Archive Authority
    foot_y = height - m - 45
    draw.text((m + 35, foot_y), "DAILY MOTIVATION ARCHIVE", font=font_footer, fill=(115, 120, 135, 220))
    handle = twitter_config.handle
    h_bbox = draw.textbbox((0, 0), handle, font=font_footer)
    draw.text((width - m - 35 - (h_bbox[2] - h_bbox[0]), foot_y), handle, font=font_footer, fill=primary_gold + (230,))

    base.convert("RGB").save(output_path, "PNG", quality=95)
    print(f"[Graphics] Rendered Obsidian Framework Card: {output_path}")
    return output_path


def render_card_for_today(entry: Dict[str, Any], weekday_idx: int, output_path: Optional[str] = None) -> str:
    """Render the flagship card for today (Obsidian Luxury Framework Card)."""
    return render_obsidian_framework_card(entry, output_path)


# Backward-compatible style aliases
render_obsidian_card = render_obsidian_framework_card
render_cosmic_card = render_obsidian_framework_card
