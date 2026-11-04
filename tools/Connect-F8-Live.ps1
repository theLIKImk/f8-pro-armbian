param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[a-zA-Z0-9.-]+$')]
    [string]$Address
)
$taskKey = '/var/tmp/f8-pro-archlinux-20261027/private-keys/f8-pro-test-ed25519'
$taskHosts = '/var/tmp/f8-pro-archlinux-20261027/test-known-hosts'
& wsl -d rg35xx-build -u root -- ssh -i $taskKey -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o HostKeyAlias=192.168.1.227 -o "UserKnownHostsFile=$taskHosts" "f8test@$Address"
exit $LASTEXITCODE
