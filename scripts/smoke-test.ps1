$ErrorActionPreference = "Stop"

$backendPort = if ($env:BACKEND_PORT) { $env:BACKEND_PORT } else { "8080" }
$dbApiPort = if ($env:DB_API_PORT) { $env:DB_API_PORT } else { "8081" }
$frontendPort = if ($env:FRONTEND_PORT) { $env:FRONTEND_PORT } else { "3000" }
$multimodalPort = if ($env:MULTIMODAL_SERVICE_PORT) { $env:MULTIMODAL_SERVICE_PORT } else { "8002" }
$sandboxPort = if ($env:SANDBOX_SERVICE_PORT) { $env:SANDBOX_SERVICE_PORT } else { "8003" }

$backendUrl = "http://localhost:$backendPort/api/v1/url-analysis"
$dbApiUrl = "http://localhost:$dbApiPort/api"
$requiredServices = @(
    "database", "db-api", "ml-service", "sandbox",
    "multimodal-service", "backend", "frontend"
)

function Invoke-Analysis([string]$Url) {
    $body = @{ url = $Url } | ConvertTo-Json
    $result = Invoke-RestMethod -Uri $backendUrl -Method Post -ContentType "application/json" -Body $body -TimeoutSec 75

    foreach ($field in @("id", "riskScore", "finalResult", "mlResult", "multimodalResult", "xaiResult")) {
        if ($null -eq $result.$field -or [string]::IsNullOrWhiteSpace([string]$result.$field)) {
            throw "분석 응답에 $field 필드가 없습니다."
        }
    }

    $stored = Invoke-RestMethod -Uri "$dbApiUrl/analyze/$($result.id)" -TimeoutSec 15
    if ($stored.id -ne $result.id -or $stored.url -ne $Url) {
        throw "DB 저장 후 조회한 결과가 분석 응답과 일치하지 않습니다."
    }

    return $stored
}

Write-Host "[1/7] 필수 컨테이너와 health 상태 확인"
$runningServices = @(docker compose ps --status running --services)
foreach ($service in $requiredServices) {
    if ($runningServices -notcontains $service) {
        throw "$service 컨테이너가 실행 중이 아닙니다."
    }
}

$unhealthy = @()
for ($attempt = 1; $attempt -le 30; $attempt++) {
    $unhealthy = @(docker compose ps --format json | ConvertFrom-Json | Where-Object { $_.Health -and $_.Health -ne "healthy" })
    if (-not $unhealthy) {
        break
    }
    Start-Sleep -Seconds 2
}
if ($unhealthy) {
    throw "60초 안에 healthy가 되지 않은 컨테이너가 있습니다: $($unhealthy.Service -join ', ')"
}

Write-Host "[2/7] frontend HTTP 응답 확인"
$frontendResponse = Invoke-WebRequest -UseBasicParsing -Uri "http://localhost:$frontendPort/" -TimeoutSec 15
if ($frontendResponse.StatusCode -ne 200) {
    throw "frontend가 HTTP 200을 반환하지 않았습니다."
}

Write-Host "[3/7] 정상 URL 분석 및 DB 조회 확인"
$normal = Invoke-Analysis "https://example.com"

Write-Host "[4/7] 안전한 합성 의심 URL 분석 및 DB 조회 확인"
$suspicious = Invoke-Analysis "https://example.com/secure-bank-login?verify=account"

Write-Host "[5/7] 내부 주소 차단 확인"
$blocked = $false
try {
    $body = @{ url = "http://localhost:3001" } | ConvertTo-Json
    Invoke-RestMethod -Uri "http://localhost:$sandboxPort/analyze" -Method Post -ContentType "application/json" -Body $body -TimeoutSec 15
} catch {
    $statusCode = [int]$_.Exception.Response.StatusCode
    if ($statusCode -eq 400 -and $_.ErrorDetails.Message -match "PRIVATE_ADDRESS_BLOCKED") {
        $blocked = $true
    }
}
if (-not $blocked) {
    throw "sandbox가 내부 주소를 차단하지 않았습니다."
}

Write-Host "[6/7] Gemini 설정 또는 503 fallback 확인"
$multimodalHealth = Invoke-RestMethod -Uri "http://localhost:$multimodalPort/health" -TimeoutSec 15
if (-not $multimodalHealth.gemini_api_key_configured) {
    $fallbackVerified = $false
    try {
        $pixel = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
        $body = @{
            url = "https://example.com"
            screenshot_base64 = $pixel
            html = "<html><body>safe fixture</body></html>"
        } | ConvertTo-Json
        Invoke-RestMethod -Uri "http://localhost:$multimodalPort/v1/analyze" -Method Post -ContentType "application/json" -Body $body -TimeoutSec 15
    } catch {
        if ([int]$_.Exception.Response.StatusCode -eq 503) {
            $fallbackVerified = $true
        }
    }
    if (-not $fallbackVerified) {
        throw "GEMINI_API_KEY 미설정 시 503 fallback을 확인하지 못했습니다."
    }
    Write-Host "Gemini 키 미설정: 503 fallback 확인 완료"
} else {
    $multimodalStored = $suspicious.multimodalResult | ConvertFrom-Json
    if ($multimodalStored.analysis_id) {
        Write-Host "Gemini 키 설정됨: 합성 의심 URL의 실제 멀티모달 결과 저장 확인"
    } else {
        Write-Host "Gemini 키 설정됨: 합성 의심 URL은 Sandbox/멀티모달 fallback으로 ML 결과 저장 완료"
    }
}

Write-Host "[7/7] 제보 API 확인"
$reportBody = @{ url = "https://example.com"; reason = "local integration smoke test" } | ConvertTo-Json
$report = Invoke-RestMethod -Uri "$dbApiUrl/reports" -Method Post -ContentType "application/json" -Body $reportBody -TimeoutSec 15
if (-not $report.id) {
    throw "제보 API가 저장 id를 반환하지 않았습니다."
}

Write-Host "전체 smoke test 성공"
Write-Host "normal: id=$($normal.id), riskScore=$($normal.riskScore), finalResult=$($normal.finalResult)"
Write-Host "synthetic: id=$($suspicious.id), riskScore=$($suspicious.riskScore), finalResult=$($suspicious.finalResult)"
