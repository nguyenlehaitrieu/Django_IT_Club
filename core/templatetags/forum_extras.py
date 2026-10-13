
import re

from django import template
from django.templatetags.static import static
from django.utils.html import escape, format_html, linebreaks
from django.utils.safestring import mark_safe

register = template.Library()

STICKERS = {
    "thanks": {
        "file": "core/images/forum-stickers/thanks.webp",
        "alt": "Cảm ơn",
    },
    "coding": {
        "file": "core/images/forum-stickers/coding.webp",
        "alt": "Đang code",
    },
    "celebrate": {
        "file": "core/images/forum-stickers/celebrate.webp",
        "alt": "Ăn mừng",
    },
    "thinking": {
        "file": "core/images/forum-stickers/thinking.webp",
        "alt": "Đang suy nghĩ",
    },
    "love": {
        "file": "core/images/forum-stickers/love.webp",
        "alt": "Yêu thích",
    },
}

STICKER_PATTERN = re.compile(r"\[sticker:([a-z_]+)\]")


@register.filter
def forum_comment_content(value):
    """Hiển thị văn bản và sticker từ danh sách cho phép."""
    text = str(value or "")
    parts = []
    last_end = 0

    for match in STICKER_PATTERN.finditer(text):
        # Văn bản bình thường được escape và giữ xuống dòng.
        before = text[last_end:match.start()]
        if before:
            parts.append(linebreaks(escape(before)))

        sticker = STICKERS.get(match.group(1))

        if sticker:
            parts.append(
                format_html(
                    '<img class="forum-comment-sticker" src="{}" '
                    'alt="{}" loading="lazy">',
                    static(sticker["file"]),
                    sticker["alt"],
                )
            )
        else:
            # Mã không hợp lệ được hiển thị như văn bản bình thường.
            parts.append(escape(match.group(0)))

        last_end = match.end()

    remaining = text[last_end:]
    if remaining:
        parts.append(linebreaks(escape(remaining)))

    return mark_safe("".join(str(part) for part in parts))
