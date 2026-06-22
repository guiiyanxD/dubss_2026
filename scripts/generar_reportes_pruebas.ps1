param(
    [string]$ComposeCommand = "docker-compose"
)

$ErrorActionPreference = "Stop"

New-Item -ItemType Directory -Force -Path "reports" | Out-Null

& $ComposeCommand exec -T web coverage run -m pytest --junitxml=reports/pytest-junit.xml
& $ComposeCommand exec -T web coverage xml -o coverage.xml
& $ComposeCommand exec -T web coverage html -d reports/coverage-html
& $ComposeCommand exec -T web coverage report | Tee-Object -FilePath reports/coverage-summary.txt

$junit = [xml](Get-Content reports/pytest-junit.xml)
$suite = $junit.testsuites.testsuite
$tests = [int]$suite.tests
$failures = [int]$suite.failures
$errors = [int]$suite.errors
$skipped = [int]$suite.skipped
$passed = $tests - $failures - $errors - $skipped
$status = if (($failures + $errors) -eq 0) { "OK" } else { "CON FALLAS" }
$generatedAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

@"
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Reporte de pruebas - DUBSS</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 32px; color: #172033; background: #f7f8fb; }
    main { max-width: 980px; margin: 0 auto; background: white; padding: 28px; border: 1px solid #dfe3eb; }
    h1 { margin-top: 0; }
    .status { display: inline-block; padding: 8px 12px; border-radius: 6px; color: white; background: #197642; font-weight: 700; }
    .status.bad { background: #a83232; }
    .grid { display: grid; grid-template-columns: repeat(4, minmax(120px, 1fr)); gap: 12px; margin: 24px 0; }
    .metric { border: 1px solid #dfe3eb; padding: 14px; border-radius: 6px; background: #fbfcff; }
    .metric strong { display: block; font-size: 28px; margin-bottom: 4px; }
    a { color: #0b5cad; }
    code { background: #eef2f7; padding: 2px 5px; border-radius: 4px; }
  </style>
</head>
<body>
<main>
  <h1>Reporte de pruebas - DUBSS</h1>
  <p>Generado: $generatedAt</p>
  <p><span class="status $(if ($status -eq "OK") { "" } else { "bad" })">$status</span></p>
  <section class="grid">
    <div class="metric"><strong>$tests</strong>Total</div>
    <div class="metric"><strong>$passed</strong>Pasadas</div>
    <div class="metric"><strong>$failures</strong>Fallidas</div>
    <div class="metric"><strong>$errors</strong>Errores</div>
  </section>
  <h2>Artefactos descargables</h2>
  <ul>
    <li><a href="pytest-junit.xml">JUnit XML de pytest</a></li>
    <li><a href="coverage-summary.txt">Resumen de cobertura</a></li>
    <li><a href="coverage-html/index.html">Reporte visual de cobertura HTML</a></li>
    <li><a href="../coverage.xml">Coverage XML para SonarQube</a></li>
  </ul>
  <h2>Comandos usados</h2>
  <pre><code>$ComposeCommand exec -T web coverage run -m pytest --junitxml=reports/pytest-junit.xml
$ComposeCommand exec -T web coverage xml -o coverage.xml
$ComposeCommand exec -T web coverage html -d reports/coverage-html</code></pre>
</main>
</body>
</html>
"@ | Set-Content -Encoding UTF8 reports/index.html

Write-Host "Reporte visual generado en reports/index.html"
Write-Host "Cobertura HTML generada en reports/coverage-html/index.html"
