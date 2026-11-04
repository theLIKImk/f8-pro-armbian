param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[a-zA-Z0-9.-]+$')]
    [string]$Address,
    [ValidatePattern('^[A-Za-z]:\\?$')]
    [string]$LogDrive
)
$ErrorActionPreference = 'Stop'
if ($LogDrive) {
$taskPub = Join-Path $LogDrive 'SSHKEY.PUB'
if (-not (Test-Path -LiteralPath $taskPub)) { throw '日志盘缺少 SSHKEY.PUB，请等待 F8ADT1 日志生成。' }
$taskRegister = Join-Path $PSScriptRoot 'register-f8-desktop-hostkey.py'
$taskPublicText = (Get-Content -LiteralPath $taskPub -Raw).Trim()
$taskPublicBase64 = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes($taskPublicText))
$taskWslScript = (& wsl -d rg35xx-build -u root -- wslpath -u $taskRegister).Trim()
if ($LASTEXITCODE -ne 0) { throw '无法转换脚本路径' }
& wsl -d rg35xx-build -u root -- python3 $taskWslScript --key-base64 $taskPublicBase64
if ($LASTEXITCODE -ne 0) { throw '主机公钥验证失败' }
} else {
    & wsl -d rg35xx-build -u root -- test -s /var/tmp/f8-pro-armbian/desktop-t1-known-hosts
    if ($LASTEXITCODE -ne 0) { throw '首次连接请通过 -LogDrive 指定物理日志盘以验证主机公钥。' }
}
& wsl -d rg35xx-build -u root -- ssh -i /var/tmp/f8-pro-archlinux-20261027/private-keys/f8-pro-test-ed25519 -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o HostKeyAlias=f8-desktop-t1 -o UserKnownHostsFile=/var/tmp/f8-pro-armbian/desktop-t1-known-hosts "f8test@$Address"
exit $LASTEXITCODE
