# Origin probe - check installation, COM and version
# Usage: powershell -ExecutionPolicy Bypass -File probe.ps1

$ErrorActionPreference = "Stop"

Write-Output "== installation =="
$roots = @("C:\Program Files\OriginLab", "C:\Program Files (x86)\OriginLab")
foreach ($r in $roots) {
    if (Test-Path $r) {
        Get-ChildItem $r -Directory | ForEach-Object { Write-Output ("  " + $_.FullName) }
    }
}

Write-Output "== COM registration =="
foreach ($id in @("Origin.ApplicationSI", "Origin.Application")) {
    $k = "Registry::HKEY_CLASSES_ROOT\$id"
    if (Test-Path $k) { Write-Output "  $id : registered" } else { Write-Output "  $id : missing" }
}

Write-Output "== live session =="
try {
    $app = New-Object -ComObject Origin.ApplicationSI
    $app.Visible = 0
    $ok = $app.Execute('type -a `"probe`";')
    Write-Output "  COM connect: OK"
    Write-Output "  Execute test: $ok"
    Write-Output ("  nplots on empty layer: " + $app.Evaluate("layer.nplots"))
    $app.Exit()
    Write-Output "  closed cleanly"
} catch {
    Write-Output "  COM connect FAILED: $($_.Exception.Message)"
    exit 1
}

Write-Output "== notes =="
Write-Output "  Origin is single-instance; close it before batch runs."
Write-Output "  Evaluate() returns a sentinel (-1.23e-300) for invalid expressions,"
Write-Output "  not an error. Verify by exporting a file and checking it exists."
