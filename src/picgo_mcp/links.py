"""把图片直链转换成常见的文档引用格式。"""
from __future__ import annotations

from html import escape


def build_links(url: str, alt_text: str) -> dict[str, str]:
    """根据上传直链生成 URL、Markdown、HTML 和 BBCode。"""
    safe_alt = alt_text.replace("\\", "\\\\").replace("]", "\\]")
    return {
        "url": url,
        "markdown": f"![{safe_alt}]({url})",
        "html": f'<img src="{escape(url, quote=True)}" alt="{escape(alt_text, quote=True)}">',
        "bbcode": f"[img]{url}[/img]",
    }
