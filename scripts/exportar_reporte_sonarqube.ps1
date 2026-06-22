param(
    [string]$SonarUrl = "http://localhost:9000",
    [string]$ProjectKey = "becas-universitarias",
    [string]$AdminPassword = "Admin12345!Dubss"
)

$ErrorActionPreference = "Stop"

New-Item -ItemType Directory -Force -Path "reports" | Out-Null

$auth = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("admin:$AdminPassword"))
$headers = @{ Authorization = "Basic $auth" }

$qualityGate = Invoke-RestMethod -Headers $headers -Uri "$SonarUrl/api/qualitygates/project_status?projectKey=$ProjectKey"
$measures = Invoke-RestMethod -Headers $headers -Uri "$SonarUrl/api/measures/component?component=$ProjectKey&metricKeys=coverage,tests,test_success_density,test_failures,test_errors,vulnerabilities,security_hotspots,bugs,code_smells,ncloc,complexity"
$vulnerabilities = Invoke-RestMethod -Headers $headers -Uri "$SonarUrl/api/issues/search?componentKeys=$ProjectKey&types=VULNERABILITY&ps=500"
$hotspots = Invoke-RestMethod -Headers $headers -Uri "$SonarUrl/api/hotspots/search?projectKey=$ProjectKey&ps=500"

$qualityGate | ConvertTo-Json -Depth 20 | Set-Content -Encoding UTF8 reports/sonarqube-quality-gate.json
$measures | ConvertTo-Json -Depth 20 | Set-Content -Encoding UTF8 reports/sonarqube-measures.json
$vulnerabilities | ConvertTo-Json -Depth 20 | Set-Content -Encoding UTF8 reports/sonarqube-vulnerabilities.json
$hotspots | ConvertTo-Json -Depth 20 | Set-Content -Encoding UTF8 reports/sonarqube-hotspots.json

$measureMap = @{}
foreach ($m in $measures.component.measures) {
    $measureMap[$m.metric] = $m.value
}

$vulnRows = ($vulnerabilities.issues | Select-Object -First 20 | ForEach-Object {
    "<tr><td>$($_.severity)</td><td>$($_.rule)</td><td>$($_.component -replace [regex]::Escape($ProjectKey + ':'), ''):$($_.line)</td><td>$($_.message)</td></tr>"
}) -join "`n"

$hotspotRows = ($hotspots.hotspots | Select-Object -First 20 | ForEach-Object {
    "<tr><td>$($_.vulnerabilityProbability)</td><td>$($_.securityCategory)</td><td>$($_.component -replace [regex]::Escape($ProjectKey + ':'), ''):$($_.line)</td><td>$($_.message)</td></tr>"
}) -join "`n"

$generatedAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

@"
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Reporte SonarQube - DUBSS</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 32px; color: #172033; background: #f7f8fb; }
    main { max-width: 1180px; margin: 0 auto; background: white; padding: 28px; border: 1px solid #dfe3eb; }
    h1 { margin-top: 0; }
    .status { display: inline-block; padding: 8px 12px; border-radius: 6px; color: white; background: #197642; font-weight: 700; }
    .grid { display: grid; grid-template-columns: repeat(4, minmax(130px, 1fr)); gap: 12px; margin: 24px 0; }
    .metric { border: 1px solid #dfe3eb; padding: 14px; border-radius: 6px; background: #fbfcff; }
    .metric strong { display: block; font-size: 28px; margin-bottom: 4px; }
    table { width: 100%; border-collapse: collapse; margin: 12px 0 24px; }
    th, td { border: 1px solid #dfe3eb; padding: 8px; text-align: left; vertical-align: top; }
    th { background: #eef2f7; }
    a { color: #0b5cad; }
  </style>
</head>
<body>
<main>
  <h1>Reporte SonarQube - DUBSS</h1>
  <p>Generado: $generatedAt</p>
  <p><span class="status">Quality Gate: $($qualityGate.projectStatus.status)</span></p>
  <p>Dashboard visual: <a href="$SonarUrl/dashboard?id=$ProjectKey">$SonarUrl/dashboard?id=$ProjectKey</a></p>

  <section class="grid">
    <div class="metric"><strong>$($measureMap.tests)</strong>Tests</div>
    <div class="metric"><strong>$($measureMap.test_success_density)%</strong>Éxito tests</div>
    <div class="metric"><strong>$($measureMap.coverage)%</strong>Cobertura Sonar</div>
    <div class="metric"><strong>$($measureMap.vulnerabilities)</strong>Vulnerabilidades</div>
    <div class="metric"><strong>$($measureMap.security_hotspots)</strong>Hotspots</div>
    <div class="metric"><strong>$($measureMap.bugs)</strong>Bugs</div>
    <div class="metric"><strong>$($measureMap.code_smells)</strong>Code smells</div>
    <div class="metric"><strong>$($measureMap.complexity)</strong>Complejidad</div>
  </section>

  <h2>Vulnerabilidades abiertas (primeras 20)</h2>
  <table>
    <thead><tr><th>Severidad</th><th>Regla</th><th>Ubicación</th><th>Mensaje</th></tr></thead>
    <tbody>$vulnRows</tbody>
  </table>

  <h2>Security hotspots a revisar (primeros 20)</h2>
  <table>
    <thead><tr><th>Probabilidad</th><th>Categoría</th><th>Ubicación</th><th>Mensaje</th></tr></thead>
    <tbody>$hotspotRows</tbody>
  </table>

  <h2>Artefactos descargables</h2>
  <ul>
    <li><a href="sonarqube-quality-gate.json">Quality Gate JSON</a></li>
    <li><a href="sonarqube-measures.json">Métricas JSON</a></li>
    <li><a href="sonarqube-vulnerabilities.json">Vulnerabilidades JSON</a></li>
    <li><a href="sonarqube-hotspots.json">Security hotspots JSON</a></li>
  </ul>
</main>
</body>
</html>
"@ | Set-Content -Encoding UTF8 reports/sonarqube-summary.html

Write-Host "Reporte SonarQube exportado en reports/sonarqube-summary.html"
