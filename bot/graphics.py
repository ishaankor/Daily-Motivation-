"""Graphics rendering engine for Formula 2: Apple Notes Dark Mode cards.
Engineered for raw, authentic, high-shareability text screenshots on Twitter/X (NO corporate plaques, NO numbered boxes).
"""

import os
import time
from typing import Dict, Any, Optional, List
from PIL import Image, ImageDraw, ImageFont

from bot.config import paths, twitter_config



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


def render_apple_notes_card(
    entry: Dict[str, Any],
    output_path: Optional[str] = None,
    width: int = 1080,
    height: int = 1350
) -> str:
    """
    Render a sleek, authentic Apple Notes Dark Mode screenshot card.
    Displays pure conversational Formula 2 narrative text with zero corporate plaques or numbered boxes.
    """
    if not output_path:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(paths.output_dir, f"notes_card_{timestamp}.png")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # 1. Base Canvas - Deep Apple Dark Gray
    base = Image.new("RGBA", (width, height), (24, 24, 26, 255))
    draw = ImageDraw.Draw(base)

    # 2. Main Apple Notes Window Container
    m = 50
    card_rect = [m, m, width - m, height - m]
    draw.rounded_rectangle(
        card_rect,
        radius=36,
        fill=(32, 32, 36, 255),
        outline=(54, 54, 58, 255),
        width=1
    )

    # 3. Typography Loading
    font_back = get_font(["Inter.ttf", "HelveticaNeue.ttc", "Avenir.ttc"], 30)
    font_meta = get_font(["Inter.ttf", "HelveticaNeue.ttc"], 22)
    font_body = get_font(["Inter.ttf", "HelveticaNeue.ttc", "Charter.ttc"], 46)
    font_punchline = get_font(["Inter.ttf", "HelveticaNeue-Bold.ttc"], 48)
    font_footer = get_font(["Inter.ttf", "HelveticaNeue.ttc"], 20)

    # 4. Top Navigation Bar (Classic iOS Notes)
    top_y = m + 36
    # Left back navigation "< Notes"
    apple_yellow = (235, 175, 60, 255)  # Apple Notes iconic yellow
    draw.text((m + 40, top_y), "<  Notes", font=font_back, fill=apple_yellow)

    # Center-right timestamp
    now = time.localtime()
    date_str = time.strftime("%B %d, %Y at %I:%M %p", now).replace(" 0", " ")
    bbox_date = draw.textbbox((0, 0), date_str, font=font_meta)
    date_w = bbox_date[2] - bbox_date[0]
    draw.text((width - m - 40 - date_w, top_y + 6), date_str, font=font_meta, fill=(142, 142, 147, 255))

    # Fine iOS divider line
    div_y = top_y + 60
    draw.line([(m + 35, div_y), (width - m - 35, div_y)], fill=(48, 48, 52, 255), width=1)

    # 5. Extract Narrative Paragraphs
    content = entry.get("tweet_1") or entry.get("hook") or entry.get("quote", "")
    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [
            "Just spent 35 minutes completely reorganizing my spice rack alphabetically to avoid writing one proposal.",
            "The paprika is organized. The client is still waiting.",
            "Step away from the seasonings. Open the document. Finish the draft."
        ]

    # 6. Render Paragraphs with natural line height and spacing
    text_x = m + 60
    max_text_w = width - (m * 2) - 120
    text_y = div_y + 75
    line_spacing = 70
    para_gap = 50

    for idx, para in enumerate(paragraphs):
        # Last paragraph is the punchline / reality check
        is_last = (idx == len(paragraphs) - 1)
        curr_font = font_punchline if is_last else font_body
        curr_color = (255, 255, 255, 255) if is_last else (235, 235, 240, 255)

        lines = wrap_text(para, curr_font, max_text_w, draw)

        # Subtle vertical yellow bar on the punchline paragraph
        if is_last and len(paragraphs) > 1:
            bar_top = text_y - 4
            bar_h = len(lines) * line_spacing + 4
            draw.rounded_rectangle(
                [text_x - 22, bar_top, text_x - 14, bar_top + bar_h],
                radius=4,
                fill=apple_yellow
            )

        for line in lines:
            draw.text((text_x, text_y), line, font=curr_font, fill=curr_color)
            text_y += line_spacing

        text_y += para_gap

    # 7. Bottom iOS Notes Status Bar
    foot_y = height - m - 45
    draw.text((m + 45, foot_y), "Notes", font=font_footer, fill=(110, 110, 115, 255))
    handle = twitter_config.handle
    bbox_h = draw.textbbox((0, 0), handle, font=font_footer)
    draw.text((width - m - 45 - (bbox_h[2] - bbox_h[0]), foot_y), handle, font=font_footer, fill=apple_yellow)

    base.convert("RGB").save(output_path, "PNG", quality=95)
    print(f"[Graphics] Rendered Apple Notes Card: {output_path}")
    return output_path


def render_card_for_today(entry: Dict[str, Any], weekday_idx: int = 0, output_path: Optional[str] = None) -> str:
    """Render the flagship card for today (Apple Notes Dark Mode Card)."""
    return render_apple_notes_card(entry, output_path)


# Backward-compatible style aliases
render_obsidian_card = render_apple_notes_card
render_cosmic_card = render_apple_notes_card
render_obsidian_framework_card = render_apple_notes_card
