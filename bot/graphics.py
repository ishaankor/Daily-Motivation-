"""Graphics rendering engine for Authentic iOS Apple Notes Dark Mode screenshots.
Engineered for zero-branding, raw iPhone Notes screenshot realism (vector '< Notes' nav, centered timestamp,
bold note title, interactive iOS checklist circles ○/●, dynamic crop height, NO bot watermarks).
"""

import os
import re
import time
from typing import Dict, Any, Optional, List, Tuple
from PIL import Image, ImageDraw, ImageFont

from bot.config import paths


def get_font(font_names: List[str], size: int) -> ImageFont.ImageFont:
    """Load font from assets/fonts first, then search system paths, with fallback."""
    font_dir = os.path.join(paths.base_dir, "assets", "fonts")
    if os.path.exists(font_dir):
        for name in font_names:
            local_path = os.path.join(font_dir, name)
            if os.path.exists(local_path):
                try:
                    return ImageFont.truetype(local_path, size)
                except Exception:
                    pass

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
    """Word wrap text to fit cleanly within max_width."""
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


def _parse_checklist_line(line: str) -> Tuple[Optional[str], str]:
    """
    Detect if a line is an iOS Notes checklist item.
    Returns ('unchecked' | 'checked' | None, cleaned_text).
    """
    stripped = line.strip()
    if stripped.startswith(("○ ", "◯ ", "- [ ] ", "[ ] ")):
        cleaned = re.sub(r"^(○|◯|- \[ \]|\[ \])\s+", "", stripped)
        return "unchecked", cleaned
    if stripped.startswith(("● ", "✓ ", "✔ ", "- [x] ", "- [X] ", "[x] ")):
        cleaned = re.sub(r"^(●|✓|✔|- \[[xX]\]|\[[xX]\])\s+", "", stripped)
        return "checked", cleaned
    return None, stripped


def render_apple_notes_card(
    entry: Dict[str, Any],
    output_path: Optional[str] = None,
    width: int = 1080,
    height: int = 1350
) -> str:
    """
    Render an authentic, unbranded iOS Apple Notes Dark Mode screenshot.
    - Pure #1C1C1E edge-to-edge iOS dark canvas (no artificial inner card border, no @handle promo footer)
    - Crisp vector '< Notes' back chevron + 'Done' button in iOS Notes Yellow (#FFD60A)
    - Centered iOS timestamp ('Today at 11:42 PM') in #8E8E93
    - Automatic bold title styling on first block + native iOS checklist circles (○ / ●)
    - Dynamic vertical crop so the screenshot hugs the note naturally like a real phone crop
    """
    if not output_path:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(paths.output_dir, f"notes_card_{timestamp}.png")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Scratch draw surface for layout measurement
    scratch = Image.new("RGBA", (width, 2000), (28, 28, 30, 255))
    sdraw = ImageDraw.Draw(scratch)

    # Typography (SF Pro / Helvetica Neue / Inter fallback)
    font_nav = get_font(["SFNS.ttf", "HelveticaNeue.ttc", "Inter.ttf", "Avenir.ttc"], 34)
    font_nav_bold = get_font(["HelveticaNeue-Bold.ttc", "Inter.ttf", "SFNS.ttf"], 34)
    font_timestamp = get_font(["SFNS.ttf", "HelveticaNeue.ttc", "Inter.ttf"], 25)
    font_title = get_font(["HelveticaNeue-Bold.ttc", "Arial Bold.ttf", "Inter.ttf"], 50)
    font_body = get_font(["SFNS.ttf", "HelveticaNeue.ttc", "Inter.ttf"], 43)
    font_body_bold = get_font(["HelveticaNeue-Bold.ttc", "Arial Bold.ttf", "Inter.ttf"], 44)

    # Colors (Exact iOS 17/18 Dark Mode Notes palette)
    ios_bg = (28, 28, 30, 255)            # #1C1C1E
    ios_yellow = (245, 194, 66, 255)      # #F5C242
    ios_grey = (142, 142, 147, 255)       # #8E8E93
    ios_text_white = (242, 242, 247, 255) # #F2F2F7
    ios_text_bright = (255, 255, 255, 255)

    # Extract raw lines / blocks from card_text
    content = (
        entry.get("card_text")
        or entry.get("quote")
        or entry.get("hook")
        or entry.get("tweet_1")
        or ""
    ).strip()
    if not content:
        content = (
            "hard pill to swallow:\n\n"
            "you procrastinate until the last minute on purpose so you have a built-in excuse if the result is mediocre."
        )

    raw_blocks = [b.strip() for b in content.split("\n\n") if b.strip()]

    pad_x = 76
    max_text_w = width - (pad_x * 2)
    checklist_indent = 64

    # Pre-calculate layout height for dynamic screenshot cropping
    cursor_y = 215
    rendered_elements = []

    for b_idx, block in enumerate(raw_blocks):
        sublines = [s.strip() for s in block.split("\n") if s.strip()]
        is_first_short_title = (
            b_idx == 0
            and len(raw_blocks) > 1
            and len(sublines) == 1
            and len(sublines[0]) <= 68
            and _parse_checklist_line(sublines[0])[0] is None
        )

        if is_first_short_title:
            w_lines = wrap_text(sublines[0], font_title, max_text_w, sdraw)
            rendered_elements.append(("title", w_lines, cursor_y))
            cursor_y += len(w_lines) * 66 + 38
            continue

        for s_idx, sub in enumerate(sublines):
            check_state, clean_sub = _parse_checklist_line(sub)
            if check_state:
                use_font = font_body_bold if check_state == "checked" else font_body
                w_lines = wrap_text(clean_sub, use_font, max_text_w - checklist_indent, sdraw)
                rendered_elements.append(("checklist", (check_state, w_lines, use_font), cursor_y))
                cursor_y += len(w_lines) * 60 + 22
            else:
                is_closing_punch = (b_idx == len(raw_blocks) - 1 and len(raw_blocks) >= 2 and s_idx == len(sublines) - 1)
                use_font = font_body_bold if is_closing_punch else font_body
                w_lines = wrap_text(clean_sub, use_font, max_text_w, sdraw)
                rendered_elements.append(("paragraph", (w_lines, use_font, is_closing_punch), cursor_y))
                cursor_y += len(w_lines) * 64 + 14

        cursor_y += 30

    # Dynamic height bounded between 820 and 1350 so it looks like a natural iPhone screenshot crop
    final_height = max(820, min(1350, cursor_y + 110))
    base = Image.new("RGBA", (width, final_height), ios_bg)
    draw = ImageDraw.Draw(base)

    # 1. Top Navigation Bar: Vector '<' Chevron + 'Notes' on left, 'Done' on right
    nav_y = 56
    chev_x = 52
    chev_mid_y = nav_y + 20
    # Draw crisp vector '<' chevron
    draw.line([(chev_x + 16, chev_mid_y - 15), (chev_x, chev_mid_y)], fill=ios_yellow, width=5)
    draw.line([(chev_x, chev_mid_y), (chev_x + 16, chev_mid_y + 15)], fill=ios_yellow, width=5)
    draw.text((chev_x + 30, nav_y), "Notes", font=font_nav, fill=ios_yellow)

    # Right: 'Done' in bold iOS Yellow
    done_text = "Done"
    done_bbox = draw.textbbox((0, 0), done_text, font=font_nav_bold)
    done_w = done_bbox[2] - done_bbox[0]
    draw.text((width - 56 - done_w, nav_y), done_text, font=font_nav_bold, fill=ios_yellow)

    # 2. Centered iOS Timestamp ('Today at 11:42 PM')
    now = time.localtime()
    time_part = time.strftime("%I:%M %p", now).lstrip("0")
    ts_text = f"Today at {time_part}"
    ts_bbox = draw.textbbox((0, 0), ts_text, font=font_timestamp)
    ts_w = ts_bbox[2] - ts_bbox[0]
    draw.text(((width - ts_w) // 2, 132), ts_text, font=font_timestamp, fill=ios_grey)

    # 3. Render Note Content Elements
    for kind, payload, start_y in rendered_elements:
        if kind == "title":
            y = start_y
            for line in payload:
                draw.text((pad_x, y), line, font=font_title, fill=ios_text_bright)
                y += 66
        elif kind == "checklist":
            check_state, w_lines, use_font = payload
            y = start_y
            # Draw iOS checklist circle aligned with first line of item
            cx = pad_x + 18
            cy = y + 26
            r = 16
            if check_state == "unchecked":
                draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=ios_grey, width=3)
                text_color = (210, 210, 215, 255)
            else:
                draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=ios_yellow, outline=ios_yellow)
                # Draw dark checkmark inside the yellow circle
                draw.line([(cx - 7, cy + 1), (cx - 2, cy + 7)], fill=ios_bg, width=4)
                draw.line([(cx - 2, cy + 7), (cx + 8, cy - 6)], fill=ios_bg, width=4)
                text_color = ios_text_bright

            for line in w_lines:
                draw.text((pad_x + checklist_indent, y), line, font=use_font, fill=text_color)
                y += 60
        elif kind == "paragraph":
            w_lines, use_font, is_closing_punch = payload
            y = start_y
            color = ios_text_bright if is_closing_punch else ios_text_white
            for line in w_lines:
                draw.text((pad_x, y), line, font=use_font, fill=color)
                y += 64

    base.convert("RGB").save(output_path, "PNG", quality=95)
    print(f"[Graphics] Rendered iOS Apple Notes Screenshot: {output_path}")
    return output_path


def render_card_for_today(entry: Dict[str, Any], weekday_idx: int = 0, output_path: Optional[str] = None) -> str:
    """Render the flagship card for today (Authentic iOS Apple Notes Dark Mode Screenshot)."""
    return render_apple_notes_card(entry, output_path)


# Backward-compatible style aliases
render_obsidian_card = render_apple_notes_card
render_cosmic_card = render_apple_notes_card
render_obsidian_framework_card = render_apple_notes_card
