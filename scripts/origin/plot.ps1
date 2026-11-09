# Origin plotting driver for corrosion figures
# Usage:
#   powershell -ExecutionPolicy Bypass -File plot.ps1 `
#       -Data data.csv -Out C:\out -Name fig10a `
#       -XTitle "Z' (\g(W)cm\+(2))" -YTitle "-Z'' (\g(W)cm\+(2))" `
#       [-Type line|line_symbol|scatter] [-NegateY] [-Format png|tif] [-Dpi 600] [-Template t.otp]
#
# Data contract (tidy CSV, header required):
#   x,y,group
# Each group becomes one curve; group values are used as the legend entries.

param(
    [Parameter(Mandatory = $true)][string]$Data,
    [Parameter(Mandatory = $true)][string]$Out,
    [Parameter(Mandatory = $true)][string]$Name,
    [string]$XTitle = "",
    [string]$YTitle = "",
    [ValidateSet("line", "line_symbol", "scatter")][string]$Type = "line_symbol",
    [switch]$NegateY,
    [ValidateSet("png", "tif", "pdf")][string]$Format = "png",
    [int]$Dpi = 600,
    [string]$XCol = "x",
    [string]$YCol = "y",
    [string]$GroupCol = "group",
    [string]$Template = "",
    [switch]$Square,
    [double]$XFrom = [double]::NaN,
    [double]$XTo = [double]::NaN,
    [double]$YFrom = [double]::NaN,
    [double]$YTo = [double]::NaN,
    [int]$LabelPt = 12,
    [int]$FontIndex = 2
)

$ErrorActionPreference = "Stop"
$plotCode = @{ line = 200; scatter = 201; line_symbol = 202 }[$Type]

function To-Lt([string]$s) { return $s.Replace('\', '/') }

# ---------- read and pivot -------------------------------------------------
if (-not (Test-Path $Data)) { throw "data file not found: $Data" }
$rows = Import-Csv $Data
if (-not $rows) { throw "empty csv" }
$cols = $rows[0].PSObject.Properties.Name
foreach ($need in @($XCol, $YCol, $GroupCol)) {
    if ($cols -notcontains $need) { throw "csv must contain column '$need' (found: $($cols -join ', '))" }
}

$groups = [ordered]@{}
foreach ($r in $rows) {
    $g = [string]$r.$GroupCol
    if (-not $groups.Contains($g)) { $groups[$g] = New-Object System.Collections.ArrayList }
    $y = [double]$r.$YCol
    if ($NegateY) { $y = -$y }
    [void]$groups[$g].Add(@([double]$r.$XCol, $y))
}

$nmax = ($groups.Values | ForEach-Object { $_.Count } | Measure-Object -Maximum).Maximum
$header = @()
$dataRows = @{}
for ($i = 0; $i -lt $nmax; $i++) { $dataRows[$i] = New-Object System.Collections.ArrayList }

$idx = 0
$longNames = @()
foreach ($g in $groups.Keys) {
    $longNames += $g
    $pts = $groups[$g]
    for ($i = 0; $i -lt $nmax; $i++) {
        if ($i -lt $pts.Count) {
            [void]$dataRows[$i].Add($pts[$i][0])
            [void]$dataRows[$i].Add($pts[$i][1])
        } else {
            [void]$dataRows[$i].Add("")
            [void]$dataRows[$i].Add("")
        }
    }
    $idx++
}

$headers = @()
for ($k = 1; $k -le $groups.Count; $k++) { $headers += "X$k"; $headers += "Y$k" }

if (-not (Test-Path $Out)) { New-Item -ItemType Directory -Path $Out -Force | Out-Null }
$wideCsv = Join-Path $env:TEMP ("origin_wide_" + [guid]::NewGuid().ToString("N") + ".csv")
$lines = @(($headers -join ","))
foreach ($i in 0..($nmax - 1)) { $lines += (($dataRows[$i] | ForEach-Object { $_ }) -join ",") }
Set-Content -Path $wideCsv -Value $lines -Encoding UTF8

# ---------- drive Origin ---------------------------------------------------
$app = $null
try {
    $app = New-Object -ComObject Origin.ApplicationSI
    $app.Visible = 0

    $book = "Fig_" + ($Name -replace '[^A-Za-z0-9]', '_')

    if ($Template -and (Test-Path $Template)) {
        # create a graph from the user template and plot into it
        $app.Execute("win -t plot `"$(To-Lt $Template)`";") | Out-Null
        $app.Execute("impCSV fname:=""$(To-Lt $wideCsv)"";") | Out-Null
    } else {
        $app.Execute("newbook name:=""$book"" sheet:=1;") | Out-Null
        $app.Execute("impCSV fname:=""$(To-Lt $wideCsv)"";") | Out-Null
    }

    if ([int]$app.Evaluate("wks.ncols") -ne ($groups.Count * 2)) {
        throw "import produced unexpected column count: $($app.Evaluate('wks.ncols'))"
    }

    for ($i = 0; $i -lt $groups.Count; $i++) {
        $col = ($i * 2) + 2
        $app.Execute("wks.col$col.lname`$=""$($longNames[$i])"";") | Out-Null
    }

    $ranges = @()
    for ($i = 0; $i -lt $groups.Count; $i++) {
        $xc = ($i * 2) + 1
        $yc = $xc + 1
        $ranges += "($xc,$yc)"
    }
    $plotCmd = "plotxy iy:=(" + ($ranges -join ",") + ") plot:=$plotCode;"
    $app.Execute($plotCmd) | Out-Null

    if ($XTitle) { $app.Execute("xb.text`$=""$XTitle"";") | Out-Null }
    if ($YTitle) { $app.Execute("yl.text`$=""$YTitle"";") | Out-Null }
    $app.Execute("layer.x.label.pt=$LabelPt; layer.y.label.pt=$LabelPt;") | Out-Null
    $app.Execute("layer.x.label.font=$FontIndex; layer.y.label.font=$FontIndex;") | Out-Null

    # axis limits: explicit values win, otherwise -Square derives them from data
    $maxX = 0.0
    $maxY = 0.0
    foreach ($g in $groups.Keys) {
        foreach ($pt in $groups[$g]) {
            if ([math]::Abs($pt[0]) -gt $maxX) { $maxX = [math]::Abs($pt[0]) }
            if ([math]::Abs($pt[1]) -gt $maxY) { $maxY = [math]::Abs($pt[1]) }
        }
    }
    $xf = if ([double]::IsNaN($XFrom)) { 0 } else { $XFrom }
    $xt = if ([double]::IsNaN($XTo)) { $maxX * 1.05 } else { $XTo }
    $yf = if ([double]::IsNaN($YFrom)) { 0 } else { $YFrom }
    $yt = if ([double]::IsNaN($YTo)) { $maxY * 1.05 } else { $YTo }

    if ($Square) {
        $lim = [math]::Max([math]::Max($xf, $xt), [math]::Max($yf, $yt))
        $xf = 0; $yf = 0; $xt = $lim; $yt = $lim
        # make the plotting box physically square: height% = width% * pageW/pageH
        $pw = [double]$app.Evaluate("page.width")
        $ph = [double]$app.Evaluate("page.height")
        $w = 60.0
        $h = $w * ($pw / $ph)
        $app.Execute("layer.left=22; layer.top=8; layer.width=$w; layer.height=$h;") | Out-Null
    }
    $app.Execute("layer.x.from=$xf; layer.x.to=$xt; layer.y.from=$yf; layer.y.to=$yt;") | Out-Null

    $app.Execute("legendupdate;") | Out-Null

    $target = Join-Path $Out ($Name + "." + $Format)
    if (Test-Path $target) { Remove-Item $target -Force }
    # Note: expGraph in Origin 2024 rejects dpi:=; resolution follows the page size
    # of the graph. Set the page in the template, or rescale the output afterwards.
    $exp = "expGraph type:=$Format path:=""$(To-Lt $Out)/"" filename:=""$Name"" tr1:=1;"
    $app.Execute($exp) | Out-Null
    Start-Sleep -Seconds 1

    if (-not (Test-Path $target)) { throw "export did not produce $target (LabTalk returned success anyway)" }
    Write-Output ("created: {0}  ({1:N0} KB)" -f $target, ((Get-Item $target).Length / 1KB))
    Write-Output ("book: {0}  curves: {1}" -f $book, $groups.Count)
} finally {
    if ($app) { try { $app.Exit() } catch { } }
    if (Test-Path $wideCsv) { Remove-Item $wideCsv -Force -ErrorAction SilentlyContinue }
}
