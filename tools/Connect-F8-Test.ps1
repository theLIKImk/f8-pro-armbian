param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[a-zA-Z0-9.-]+$')]
    [string]$Address
)
$taskProject = Split-Path -Parent $PSScriptRoot
$taskState = Get-Content -LiteralPath (Join-Path $taskProject 'analysis\test-rootfs\integration.json') -Raw | ConvertFrom-Json
if ($taskState.private_key_path -notlike '/var/tmp/f8-pro-*/private-keys/f8-pro-test-ed25519') {
    throw 'Unexpected test key path.'
}
$taskHosts = '/var/tmp/f8-pro-archlinux-20261027/test-known-hosts'
& wsl -d rg35xx-build -u root -- ssh -i $taskState.private_key_path -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new -o "UserKnownHostsFile=$taskHosts" "alarm@$Address"
exit $LASTEXITCODE
