"""通过 PicGo Core CLI 上传本地图片。"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class UploadResult:
    """表示一次 PicGo 上传结果。"""

    file_name: str
    url: str


class PicGoError(RuntimeError):
    """描述 PicGo 命令、上传或响应解析失败。"""


def _find_image_record(output: str) -> dict[str, Any] | None:
    """从 PicGo 日志混合输出中找出 JSON 上传记录。"""
    decoder = json.JSONDecoder()
    for line in reversed(output.splitlines()):
        stripped = line.strip()
        for index, char in enumerate(stripped):
            if char not in "[{":
                continue
            try:
                payload, _ = decoder.raw_decode(stripped[index:])
            except json.JSONDecodeError:
                continue
            records = payload if isinstance(payload, list) else [payload]
            for record in records:
                if isinstance(record, dict) and (record.get("imgUrl") or record.get("url")):
                    return record
    return None


def _redact(text: str) -> str:
    """隐藏 PicGo 错误文本中可能出现的 GitHub 令牌。"""
    return re.sub(
        r"(?:gh[pousr]_[A-Za-z0-9_]{10,}|github_pat_[A-Za-z0-9_]+)",
        "[REDACTED]",
        text,
    )


def _command_for(executable: str, image_path: Path, env: dict[str, str]) -> list[str]:
    """构造跨 Windows 与 Unix 的 PicGo 子进程命令。"""
    if os.name == "nt" and Path(executable).suffix.lower() in {".cmd", ".bat"}:
        powershell = shutil.which("powershell.exe") or shutil.which("pwsh.exe")
        if not powershell:
            raise PicGoError("Windows 上执行 PicGo 命令需要 PowerShell。")
        env["PICGO_MCP_COMMAND"] = executable
        env["PICGO_MCP_FILE"] = str(image_path)
        script = (
            "$utf8 = New-Object System.Text.UTF8Encoding -ArgumentList $false; "
            "[Console]::OutputEncoding = $utf8; $OutputEncoding = $utf8; "
            "& $env:PICGO_MCP_COMMAND upload $env:PICGO_MCP_FILE --format json; "
            "exit $LASTEXITCODE"
        )
        return [powershell, "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", script]
    return [executable, "upload", str(image_path), "--format", "json"]


def upload_with_picgo(
    file_path: str | Path,
    *,
    picgo_command: str | None = None,
    timeout: float = 180,
) -> UploadResult:
    """调用 PicGo CLI 上传文件，并返回图片直链。"""
    source = Path(file_path).expanduser()
    try:
        image_path = source.resolve(strict=True)
    except OSError as exc:
        raise PicGoError(f"图片文件不存在或不可访问：{source}") from exc

    if not image_path.is_file():
        raise PicGoError(f"图片路径不是文件：{image_path}")
    if timeout <= 0:
        raise PicGoError("超时时间必须大于 0 秒。")

    command_name = picgo_command or os.environ.get("PICGO_COMMAND", "picgo")
    executable = shutil.which(command_name)
    if executable is None and Path(command_name).is_file():
        executable = str(Path(command_name).resolve())
    if executable is None:
        raise PicGoError(
            "找不到 PicGo CLI。请先安装并配置 PicGo Core，"
            "或通过 PICGO_COMMAND 指定 picgo 可执行文件路径。"
        )

    env = os.environ.copy()
    command = _command_for(executable, image_path, env)
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise PicGoError(f"PicGo 上传超过 {timeout:g} 秒，已停止等待。") from exc
    except OSError as exc:
        raise PicGoError(f"无法启动 PicGo CLI：{exc}") from exc

    combined_output = "\n".join(
        part for part in (completed.stdout, completed.stderr) if part
    )
    if completed.returncode != 0:
        detail = next(
            (line.strip() for line in reversed(combined_output.splitlines()) if line.strip()),
            "PicGo 未提供错误详情。",
        )
        raise PicGoError(
            f"PicGo 上传失败，退出码 {completed.returncode}：{_redact(detail)}"
        )

    record = _find_image_record(combined_output)
    if record is None:
        raise PicGoError("PicGo 已结束，但输出中没有可识别的图片链接。")

    url = record.get("imgUrl") or record.get("url")
    if not isinstance(url, str) or not url.startswith(("https://", "http://")):
        raise PicGoError("PicGo 返回了无效的 HTTP 图片链接。")

    file_name = record.get("fileName") or image_path.name
    return UploadResult(file_name=str(file_name), url=url)
