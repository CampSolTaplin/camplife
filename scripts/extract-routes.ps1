Add-Type -AssemblyName System.Drawing

# Color targets (RGB)
$COLORS = @{
  plaza_blue   = [System.Drawing.Color]::FromArgb(255, 30, 90, 220)
  hillel_red   = [System.Drawing.Color]::FromArgb(255, 224, 74, 74)
  playground_g = [System.Drawing.Color]::FromArgb(255, 63, 168, 118)
  eca_pink     = [System.Drawing.Color]::FromArgb(255, 255, 79, 179)
  exit_orange  = [System.Drawing.Color]::FromArgb(255, 255, 138, 31)
  gate_teal    = [System.Drawing.Color]::FromArgb(255, 31, 182, 182)
  drop_yellow  = [System.Drawing.Color]::FromArgb(255, 255, 193, 7)
}

function ColorDist($c1, $c2) {
  $dr = $c1.R - $c2.R; $dg = $c1.G - $c2.G; $db = $c1.B - $c2.B
  return $dr*$dr + $dg*$dg + $db*$db
}

function ExtractPixels {
  param($basePath, $recoPath, $target, $threshold = 5500, $diffMin = 1500, $step = 3)
  $base = New-Object System.Drawing.Bitmap($basePath)
  $reco = New-Object System.Drawing.Bitmap($recoPath)

  # Fast bitmap access via LockBits
  $rect = New-Object System.Drawing.Rectangle 0, 0, $base.Width, $base.Height
  $baseData = $base.LockBits($rect, [System.Drawing.Imaging.ImageLockMode]::ReadOnly, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
  $recoData = $reco.LockBits($rect, [System.Drawing.Imaging.ImageLockMode]::ReadOnly, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
  $stride = $baseData.Stride
  $bytes = $stride * $base.Height
  $baseBuf = New-Object byte[] $bytes
  $recoBuf = New-Object byte[] $bytes
  [System.Runtime.InteropServices.Marshal]::Copy($baseData.Scan0, $baseBuf, 0, $bytes)
  [System.Runtime.InteropServices.Marshal]::Copy($recoData.Scan0, $recoBuf, 0, $bytes)
  $base.UnlockBits($baseData); $reco.UnlockBits($recoData)

  $tR = $target.R; $tG = $target.G; $tB = $target.B
  $pts = New-Object System.Collections.Generic.List[object]
  $w = $base.Width; $h = $base.Height
  for ($y = 0; $y -lt $h; $y += $step) {
    $row = $y * $stride
    for ($x = 0; $x -lt $w; $x += $step) {
      $i = $row + ($x * 4)
      $bB = $baseBuf[$i]; $bG = $baseBuf[$i+1]; $bR = $baseBuf[$i+2]
      $rB = $recoBuf[$i]; $rG = $recoBuf[$i+1]; $rR = $recoBuf[$i+2]
      $dDiff = ($bR-$rR)*($bR-$rR) + ($bG-$rG)*($bG-$rG) + ($bB-$rB)*($bB-$rB)
      if ($dDiff -gt $diffMin) {
        $dTar = ($rR-$tR)*($rR-$tR) + ($rG-$tG)*($rG-$tG) + ($rB-$tB)*($rB-$tB)
        if ($dTar -lt $threshold) {
          $pts.Add(@{ x=$x; y=$y })
        }
      }
    }
  }
  $base.Dispose(); $reco.Dispose()
  return $pts
}

function Centroid {
  param($pts)
  if ($pts.Count -eq 0) { return $null }
  $sx = 0.0; $sy = 0.0
  foreach ($p in $pts) { $sx += $p.x; $sy += $p.y }
  return @{ x = [int]($sx / $pts.Count); y = [int]($sy / $pts.Count) }
}

function OrderPath {
  param($pts, $startNearX, $startNearY, $maxStep = 25)
  if ($pts.Count -eq 0) { return @() }
  # Find starting pixel closest to (startNearX, startNearY)
  $startIdx = 0; $bestD = [double]::MaxValue
  for ($i = 0; $i -lt $pts.Count; $i++) {
    $d = ($pts[$i].x - $startNearX) * ($pts[$i].x - $startNearX) + ($pts[$i].y - $startNearY) * ($pts[$i].y - $startNearY)
    if ($d -lt $bestD) { $bestD = $d; $startIdx = $i }
  }
  $visited = New-Object bool[] $pts.Count
  $visited[$startIdx] = $true
  $ordered = @($pts[$startIdx])
  $cur = $pts[$startIdx]
  $maxStepSq = $maxStep * $maxStep
  while ($true) {
    $bestI = -1; $bestD = [double]::MaxValue
    for ($i = 0; $i -lt $pts.Count; $i++) {
      if ($visited[$i]) { continue }
      $d = ($pts[$i].x - $cur.x) * ($pts[$i].x - $cur.x) + ($pts[$i].y - $cur.y) * ($pts[$i].y - $cur.y)
      if ($d -lt $bestD) { $bestD = $d; $bestI = $i }
    }
    if ($bestI -lt 0 -or $bestD -gt $maxStepSq) { break }
    $visited[$bestI] = $true
    $cur = $pts[$bestI]
    $ordered += $cur
  }
  return $ordered
}

function SimplifyPath {
  param($ordered, $sampleEvery = 15)
  if ($ordered.Count -eq 0) { return @() }
  $simplified = @($ordered[0])
  for ($i = $sampleEvery; $i -lt $ordered.Count - 1; $i += $sampleEvery) {
    $simplified += $ordered[$i]
  }
  $simplified += $ordered[$ordered.Count - 1]
  return $simplified
}

function ToSvgD {
  param($poly)
  if ($poly.Count -eq 0) { return "" }
  $parts = @("M $($poly[0].x) $($poly[0].y)")
  for ($i = 1; $i -lt $poly.Count; $i++) {
    $parts += "L $($poly[$i].x) $($poly[$i].y)"
  }
  return ($parts -join " ")
}

function ProcessCarpool {
  param($name, $basePath, $recoPath, $entryColor)

  Write-Host "=== $name ===" -ForegroundColor Cyan

  $dropPx = ExtractPixels $basePath $recoPath $COLORS.drop_yellow 4500 1200 2
  $gatePx = ExtractPixels $basePath $recoPath $COLORS.gate_teal  4500 1200 2
  $entryPx = ExtractPixels $basePath $recoPath $entryColor       6500 1500 3
  $exitPx  = ExtractPixels $basePath $recoPath $COLORS.exit_orange 6500 1500 3

  Write-Host ("  drop pixels: {0}, gate pixels: {1}" -f $dropPx.Count, $gatePx.Count)
  Write-Host ("  entry pixels: {0}, exit pixels: {1}" -f $entryPx.Count, $exitPx.Count)

  $drop = Centroid $dropPx
  $gate = Centroid $gatePx
  Write-Host ("  drop centroid: ({0}, {1})" -f $drop.x, $drop.y)
  Write-Host ("  gate centroid: ({0}, {1})" -f $gate.x, $gate.y)

  # Entry: walk from end farthest from drop-off, ending near drop-off
  # Strategy: pick farthest-from-drop point as start
  $bestI = 0; $bestD = 0
  for ($i = 0; $i -lt $entryPx.Count; $i++) {
    $d = ($entryPx[$i].x - $drop.x) * ($entryPx[$i].x - $drop.x) + ($entryPx[$i].y - $drop.y) * ($entryPx[$i].y - $drop.y)
    if ($d -gt $bestD) { $bestD = $d; $bestI = $i }
  }
  $sx = $entryPx[$bestI].x; $sy = $entryPx[$bestI].y
  Write-Host ("  entry start (farthest from drop): ($sx, $sy)")
  $entryOrdered = OrderPath $entryPx $sx $sy 35
  $entryPoly = SimplifyPath $entryOrdered 10
  Write-Host ("  entry ordered: {0}, simplified: {1}" -f $entryOrdered.Count, $entryPoly.Count)
  $entryD = ToSvgD $entryPoly

  # Exit: start near drop-off, end near gate
  $exitOrdered = OrderPath $exitPx $drop.x $drop.y 35
  $exitPoly = SimplifyPath $exitOrdered 10
  Write-Host ("  exit ordered: {0}, simplified: {1}" -f $exitOrdered.Count, $exitPoly.Count)
  $exitD = ToSvgD $exitPoly

  Write-Host ("  entryD: $entryD")
  Write-Host ("  exitD: $exitD")

  return @{
    name = $name
    drop = $drop
    gate = $gate
    entryD = $entryD
    exitD = $exitD
  }
}

$base = "C:\Users\arih\OneDrive - MARJCC\Desktop\camplife_handoff\Carpools"
$result = @{}
$result.scheck = ProcessCarpool "Scheck" "$base\Scheck Family Plaza BASE.png" "$base\Scheck Family Plaza Recorrido.png" $COLORS.plaza_blue
$result.hillel = ProcessCarpool "Hillel" "$base\Hillel Carpool Base.png" "$base\Hillel Carpool Recorrido.png" $COLORS.hillel_red
$result.savage = ProcessCarpool "Savage" "$base\Savage Playground BASE.png" "$base\Savage Playground Recorrido.png" $COLORS.playground_g
$result.eca    = ProcessCarpool "ECA"    "$base\ECA CARPOOL BASE.png" "$base\ECA CARPOOL Recorrido.png" $COLORS.eca_pink

$out = "C:\Users\arih\OneDrive - MARJCC\Desktop\camplife_handoff\scripts\routes.json"
$result | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 $out
Write-Host "`nWrote $out" -ForegroundColor Green
