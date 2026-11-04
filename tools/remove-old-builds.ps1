$ErrorActionPreference = 'Stop'
if (Test-Path -LiteralPath 'analysis/build-cleanup/20261102/windows-delete-result.json') { throw 'One-time cleanup already completed' }
$taskPlanPath = Join-Path (Get-Location) 'analysis/build-cleanup/20261102/windows-delete-plan.json'
$taskPlan = Get-Content -LiteralPath $taskPlanPath -Raw | ConvertFrom-Json
$taskRoot = [IO.Path]::GetFullPath((Resolve-Path -LiteralPath 'outputs').ProviderPath).TrimEnd('\')
if (-not [StringComparer]::OrdinalIgnoreCase.Equals($taskRoot, [IO.Path]::GetFullPath($taskPlan.root).TrimEnd('\'))) { throw 'Unexpected output root' }
$taskFreeBefore = (Get-Volume -DriveLetter D).SizeRemaining
$taskResults = @()
foreach ($taskEntry in $taskPlan.targets) {
    $taskTarget = [IO.Path]::GetFullPath($taskEntry.path)
    if (-not $taskTarget.StartsWith($taskRoot + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Target outside output root' }
    $taskItem = Get-Item -LiteralPath $taskTarget -Force
    if ($taskItem.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Refuse reparse target' }
    if ($taskItem.PSIsContainer) {
        $taskLinks = @(Get-ChildItem -LiteralPath $taskTarget -Force -Recurse | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint })
        if ($taskLinks.Count -ne 0) { throw 'Refuse directory containing reparse points' }
        Remove-Item -LiteralPath $taskTarget -Force -Recurse
    } else {
        Remove-Item -LiteralPath $taskTarget -Force
    }
    if (Test-Path -LiteralPath $taskTarget) { throw 'Removal incomplete' }
    $taskResults += [pscustomobject]@{ path = $taskTarget; deleted = $true }
}
$taskReport = [pscustomobject]@{ completed = $true; targets = $taskResults; drive_d_free_before = $taskFreeBefore; drive_d_free_after = (Get-Volume -DriveLetter D).SizeRemaining; tablet_touched = $false }
$taskReportPath = Join-Path (Get-Location) 'analysis/build-cleanup/20261102/windows-delete-result.json'
[IO.File]::WriteAllText($taskReportPath, ($taskReport | ConvertTo-Json -Depth 6), [Text.UTF8Encoding]::new($false))
$taskReport | Select-Object completed,drive_d_free_before,drive_d_free_after,tablet_touched | ConvertTo-Json -Compress
