# image-uploader

基于 PicGo Core 的图片上传 CLI 与 MCP server。PicGo 负责图床和上传；本项目负责命令行体验、链接格式和 MCP 工具。

~~~mermaid
flowchart LR
    CLI["picgo-link CLI"] --> Core["PicGo Core CLI"]
    MCP["picgo-mcp MCP server"] --> Core
    Core --> Host["PicGo 当前配置的图床"]
    CLI --> Links["URL / Markdown / HTML / BBCode"]
    MCP --> Links
~~~

## 环境

- Python 3.10+
- [uv](https://docs.astral.sh/uv/)
- [PicGo Core](https://github.com/PicGo/PicGo-Core)，并至少配置一个 uploader

安装 PicGo Core 并配置图床：

~~~powershell
npm install --global picgo
picgo set uploader
~~~

上传凭据保存在 PicGo 自己的本机配置中。本项目不读取或复制凭据；默认使用 PicGo 当前 uploader。若可执行文件不在 PATH，可设置 <code>PICGO_COMMAND</code> 或传入 <code>--picgo-command</code>。

## CLI

开发环境：

~~~powershell
uv sync
uv run picgo-link .\figure.png
uv run picgo-link .\figure.png --format markdown --alt "结构示意"
~~~

默认输出直链、Markdown、HTML 和 BBCode。<code>--format</code> 支持 <code>all</code>、<code>url</code>、<code>markdown</code>（简写 <code>md</code>）、<code>html</code>、<code>bbcode</code> 和 <code>json</code>。

发布到 PyPI 后，可以直接运行：

~~~powershell
uvx --from picgo-mcp picgo-link .\figure.png --format markdown
~~~

## MCP

本机开发运行：

~~~powershell
uv run picgo-mcp
~~~

MCP 使用 stdio transport，日志输出到 stderr。客户端配置示例（PyPI 发布后）：

~~~json
{
  "mcpServers": {
    "picgo-mcp": {
      "command": "uvx",
      "args": ["picgo-mcp"]
    }
  }
}
~~~

唯一工具 <code>upload_image(file_path, alt_text?)</code> 上传 MCP 主机可访问的本地文件，并返回 <code>url</code>、<code>markdown</code>、<code>html</code>、<code>bbcode</code>。文件路径必须对 MCP server 所在机器可见。

## 开发

~~~powershell
uv sync
uv run picgo-link --help
uv build
~~~

## 自动发布

GitHub Actions 在推送 <code>v*</code> 标签后构建 wheel/sdist、发布到 PyPI，并创建 GitHub Release。先在仓库的 <code>Settings → Secrets and variables → Actions</code> 中添加名为 <code>PYPI_API_TOKEN</code> 的 Secret；发布 job 通过 <code>UV_PUBLISH_TOKEN</code> 使用它，不会把密钥写进代码或构建日志。

PyPI API token 需有权创建或发布 <code>picgo-mcp</code>。PyPI 支持账户级或项目级 token；项目创建后，建议将长期 token 限定到该项目。

首次从干净的 <code>main</code> 分支运行：

~~~powershell
.\scripts\release.ps1 -Version 0.1.0
~~~

脚本构建发行包并推送首个标签；后续版本会更新版本和锁文件、提交，再推送分支与标签。GitHub Actions 自动发布 PyPI 并创建 GitHub Release。详见 [uv 发布文档](https://docs.astral.sh/uv/guides/publish/)。
