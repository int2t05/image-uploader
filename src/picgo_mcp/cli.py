"""PicGo 图片链接命令行入口。"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Sequence

from .links import build_links
from .uploader import PicGoError, upload_with_picgo


def _parser() -> argparse.ArgumentParser:
    """构造命令行参数。"""
    parser = argparse.ArgumentParser(
        prog="picgo-link",
        description="通过已配置的 PicGo 图床上传图片并输出链接格式。",
    )
    parser.add_argument("image", type=Path, help="本地图片路径")
    parser.add_argument(
        "-f",
        "--format",
        choices=("all", "url", "markdown", "md", "html", "bbcode", "json"),
        default="all",
        help="输出格式，默认 all",
    )
    parser.add_argument("--alt", help="Markdown/HTML 替代文字")
    parser.add_argument(
        "--picgo-command",
        default=os.environ.get("PICGO_COMMAND", "picgo"),
        help="PicGo 可执行文件路径，默认使用 PATH 中的 picgo",
    )
    parser.add_argument("--timeout", type=float, default=180, help="上传超时秒数")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """上传单张图片并按需打印链接格式。"""
    args = _parser().parse_args(argv)
    try:
        result = upload_with_picgo(
            args.image,
            picgo_command=args.picgo_command,
            timeout=args.timeout,
        )
    except PicGoError as exc:
        print(f"picgo-link: {exc}", file=sys.stderr)
        return 1

    links = build_links(result.url, args.alt or Path(result.file_name).stem)
    output_format = "markdown" if args.format == "md" else args.format

    if output_format == "json":
        print(
            json.dumps(
                {"file_name": result.file_name, **links},
                ensure_ascii=False,
                indent=2,
            )
        )
    elif output_format == "all":
        print(f"URL: {links['url']}")
        print(f"Markdown: {links['markdown']}")
        print(f"HTML: {links['html']}")
        print(f"BBCode: {links['bbcode']}")
    else:
        print(links[output_format])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
