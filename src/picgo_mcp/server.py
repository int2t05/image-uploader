"""PicGo MCP server，使用 stdio 与 MCP 客户端通信。"""
from __future__ import annotations

import logging
import sys

from mcp.server.mcpserver import MCPServer

from . import __version__
from .links import build_links
from .uploader import upload_with_picgo

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("picgo_mcp")
mcp = MCPServer("picgo-mcp", version=__version__)


@mcp.tool()
def upload_image(file_path: str, alt_text: str | None = None) -> dict[str, str]:
    """上传本地图片，并返回直链、Markdown、HTML 与 BBCode。"""
    result = upload_with_picgo(file_path)
    links = build_links(result.url, alt_text or result.file_name.rsplit(".", 1)[0])
    logger.info("图片上传完成：%s", result.file_name)
    return {"file_name": result.file_name, **links}


def main() -> int:
    """启动 stdio MCP server。"""
    logger.info("picgo-mcp MCP server 启动（stdio）。")
    mcp.run(transport="stdio")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
