Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$taskProject = Split-Path -Parent $PSScriptRoot
$taskNetworkPath = Join-Path $taskProject 'local\first-boot-network.json'
$taskNetworkText = [System.IO.File]::ReadAllText($taskNetworkPath)
# Pipe UTF-8 privately to WSL rather than weakening the Windows input-file ACL.
$taskStart = [System.Diagnostics.ProcessStartInfo]::new()
$taskStart.FileName = 'wsl.exe'
$taskStart.Arguments = '-d rg35xx-build -u root -- python3 /mnt/d/Netdisk/Other/F8-PRO/archlinux/tools/inject-test-network.py /var/tmp/f8-pro-archlinux-20261027/rootfs-vendor-staging -'
$taskStart.UseShellExecute = $false
$taskStart.CreateNoWindow = $true
$taskStart.RedirectStandardInput = $true
$taskStart.StandardInputEncoding = [System.Text.UTF8Encoding]::new($false)
$taskProcess = [System.Diagnostics.Process]::new()
$taskProcess.StartInfo = $taskStart
if (-not $taskProcess.Start()) { throw 'Could not start the private network injector.' }
$taskProcess.StandardInput.Write($taskNetworkText)
$taskProcess.StandardInput.Close()
$taskNetworkText = $null
$taskProcess.WaitForExit()
if ($taskProcess.ExitCode -ne 0) { throw 'Fill in the private Wi-Fi file before building.' }
& wsl -d rg35xx-build -u root -- python3 /mnt/d/Netdisk/Other/F8-PRO/archlinux/tools/build-test-image.py
if ($LASTEXITCODE -ne 0) { throw 'Image build failed; inspect the build logs.' }
& wsl -d rg35xx-build -u root -- python3 /mnt/d/Netdisk/Other/F8-PRO/archlinux/tools/verify-built-image.py wifi-test
if ($LASTEXITCODE -ne 0) { throw 'Image content verification failed.' }
& (Join-Path $PSScriptRoot 'Export-F8-Test.ps1') -Variant wifi-test
& python (Join-Path $PSScriptRoot 'unpack-test-image.py') (Join-Path $taskProject 'local\test-images\wifi-test')
if ($LASTEXITCODE -ne 0) { throw 'Raw partition image preparation failed.' }
