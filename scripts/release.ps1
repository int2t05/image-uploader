[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^\d+\.\d+\.\d+$')]
    [string] $Version
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot
$committed = $false

try {
    if (@(git status --porcelain).Count -gt 0) {
        throw '工作区必须干净；先提交或整理当前改动。'
    }

    $branch = (git branch --show-current).Trim()
    if ($branch -ne 'main') {
        throw "请从 main 分支发布，当前分支为：$branch"
    }

    $origin = (git remote get-url origin).Trim()
    if ($LASTEXITCODE -ne 0 -or $origin -notmatch '([:/])int2t05/picgo-mcp(?:\.git)?$') {
        throw 'origin 必须指向 int2t05/picgo-mcp。'
    }

    git fetch origin main --tags
    if ($LASTEXITCODE -ne 0) { throw '无法读取 GitHub 最新状态。' }

    $localHead = (git rev-parse HEAD).Trim()
    $remoteHead = (git rev-parse origin/main).Trim()
    if ($localHead -ne $remoteHead) {
        throw '本地 main 与 origin/main 不一致；先同步代码再发布。'
    }

    $currentVersion = (uv version --short).Trim()
    if ([version] $Version -le [version] $currentVersion) {
        throw "新版本 $Version 必须高于当前版本 $currentVersion。"
    }
    if (git tag --list "v$Version") {
        throw "标签 v$Version 已存在。"
    }

    uv version $Version
    if ($LASTEXITCODE -ne 0) { throw '更新 pyproject 版本失败。' }

    uv lock
    if ($LASTEXITCODE -ne 0) { throw '更新 uv.lock 失败。' }

    uv build
    if ($LASTEXITCODE -ne 0) { throw '构建失败；尚未提交或推送。' }

    git add pyproject.toml uv.lock
    git commit -m "release: v$Version"
    if ($LASTEXITCODE -ne 0) { throw '版本提交失败。' }
    $committed = $true

    git tag -a "v$Version" -m "Release v$Version"
    if ($LASTEXITCODE -ne 0) { throw '创建版本标签失败。' }

    git push origin main --follow-tags
    if ($LASTEXITCODE -ne 0) {
        throw "推送失败；本地提交和 v$Version 标签已保留，可用 git push origin main --follow-tags 重试。"
    }

    Write-Output "已推送 v$Version；GitHub Actions 将创建 Release 并发布 PyPI。"
}
catch {
    if (-not $committed) {
        git restore -- pyproject.toml uv.lock 2>$null
    }
    throw
}
finally {
    Pop-Location
}
