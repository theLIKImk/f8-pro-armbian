param(
    [ValidateSet('pending-wifi', 'wifi-test')]
    [string]$Variant = 'pending-wifi'
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$taskProject = Split-Path -Parent $PSScriptRoot
$taskSource = "\\wsl.localhost\rg35xx-build\var\tmp\f8-pro-archlinux-20261027\exports\$Variant"
$taskDestination = Join-Path $taskProject "local\test-images\$Variant"
New-Item -ItemType Directory -Path $taskDestination -Force | Out-Null
$taskManifest = Get-Content -LiteralPath (Join-Path $taskSource 'manifest.json') -Raw | ConvertFrom-Json
$taskImageName = "f8-pro-arch-$Variant.img.gz"
foreach ($taskName in @($taskImageName, 'factory-boot.img', 'manifest.json', 'SHA256SUMS', 'README.txt')) {
    Copy-Item -LiteralPath (Join-Path $taskSource $taskName) -Destination (Join-Path $taskDestination $taskName) -Force
}
$taskImageHash = (Get-FileHash -LiteralPath (Join-Path $taskDestination $taskImageName) -Algorithm SHA256).Hash.ToLowerInvariant()
$taskBootHash = (Get-FileHash -LiteralPath (Join-Path $taskDestination 'factory-boot.img') -Algorithm SHA256).Hash.ToLowerInvariant()
if ($taskImageHash -ne $taskManifest.gzip_sha256 -or $taskBootHash -ne $taskManifest.original_boot_sha256) {
    throw 'Exported file checksum mismatch.'
}
Write-Output "Export verified: $taskDestination"
