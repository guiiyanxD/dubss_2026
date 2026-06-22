param(
    [string]$ComposeCommand = "docker-compose",
    [string]$SonarUrl = "http://localhost:9000",
    [string]$AdminPassword = "Admin12345!Dubss",
    [string]$ProjectKey = "becas-universitarias",
    [string]$ProjectName = "Sistema de Gestion de Becas Universitarias"
)

$ErrorActionPreference = "Stop"

& $ComposeCommand up -d sonarqube

for ($i = 1; $i -le 90; $i++) {
    try {
        $status = Invoke-RestMethod -UseBasicParsing "$SonarUrl/api/system/status"
        if ($status.status -eq "UP") {
            break
        }
        Write-Host "SonarQube status: $($status.status)"
    }
    catch {
        Write-Host "Esperando SonarQube..."
    }
    Start-Sleep -Seconds 5
}

$defaultPair = "admin:admin"
$defaultBasic = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes($defaultPair))

try {
    Invoke-RestMethod `
        -Method Post `
        -Headers @{ Authorization = "Basic $defaultBasic" } `
        -Uri "$SonarUrl/api/users/change_password" `
        -Body @{
            login = "admin"
            previousPassword = "admin"
            password = $AdminPassword
        } | Out-Null
    Write-Host "Password default de admin actualizada."
}
catch {
    Write-Host "Password default no actualizada; probablemente ya estaba configurada."
}

$adminPair = "admin:$AdminPassword"
$adminBasic = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes($adminPair))

try {
    Invoke-RestMethod `
        -Method Post `
        -Headers @{ Authorization = "Basic $adminBasic" } `
        -Uri "$SonarUrl/api/projects/create" `
        -Body @{ name = $ProjectName; project = $ProjectKey } | Out-Null
    Write-Host "Proyecto SonarQube creado: $ProjectKey"
}
catch {
    Write-Host "Proyecto SonarQube ya existe o no pudo crearse automáticamente."
}

$tokenName = "scanner-token-dubss-$(Get-Date -Format yyyyMMddHHmmss)"
$tokenResponse = Invoke-RestMethod `
    -Method Post `
    -Headers @{ Authorization = "Basic $adminBasic" } `
    -Uri "$SonarUrl/api/user_tokens/generate" `
    -Body @{ name = $tokenName }

$token = $tokenResponse.token
$envPath = ".env"
$envContent = if (Test-Path $envPath) { Get-Content $envPath } else { @() }
$withoutToken = $envContent | Where-Object { $_ -notmatch "^SONAR_TOKEN=" }
$withoutToken + "SONAR_TOKEN=$token" | Set-Content -Encoding UTF8 $envPath

Write-Host "SONAR_TOKEN guardado en .env"
Write-Host "Dashboard: $SonarUrl/dashboard?id=$ProjectKey"
Write-Host "Ejecuta el scanner con: $ComposeCommand --profile quality run --rm sonar-scanner"
