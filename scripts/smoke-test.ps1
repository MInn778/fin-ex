$ErrorActionPreference = "Stop"
$apiUrl = "http://localhost:8080/api/v1/url-analysis"

Write-Host "[1/3] Docker 컨테이너 상태 확인"

$containers = docker compose ps --status running --services

if ($containers -notcontains "backend") {
    throw "backend 컨테이너가 실행 중이 아닙니다."
}

if ($containers -notcontains "sandbox") {
    throw "sandbox 컨테이너가 실행 중이 아닙니다."
}

Write-Host "[2/3] 정상 URL 분석 확인"

$normalBody = @{ url = "https://example.com" } | ConvertTo-Json
$normalResult = Invoke-RestMethod -Uri $apiUrl -Method Post -ContentType "application/json" -Body $normalBody

if ($normalResult.statusCode -ne 200) {
    throw "예상하지 못한 HTTP 상태: $($normalResult.statusCode)"
}

if ([string]::IsNullOrWhiteSpace($normalResult.html)) {
    throw "HTML이 반환되지 않았습니다."
}

if ([string]::IsNullOrWhiteSpace($normalResult.screenshotBase64)) {
    throw "Screenshot이 반환되지 않았습니다."
}

Write-Host "정상 URL 분석 성공"
Write-Host "제목: $($normalResult.title)"
Write-Host "HTML 크기: $($normalResult.htmlSizeBytes)"
Write-Host "Screenshot 크기: $($normalResult.screenshotSizeBytes)"

Write-Host "[3/3] 내부 주소 차단 확인"

$blockedBody = @{ url = "http://localhost:3001" } | ConvertTo-Json
$blockedSuccessfully = $false

try {
    Invoke-RestMethod -Uri $apiUrl -Method Post -ContentType "application/json" -Body $blockedBody
} catch {
    if ($_.ErrorDetails.Message -match "PRIVATE_ADDRESS_BLOCKED") {
        $blockedSuccessfully = $true
    }
}

if (-not $blockedSuccessfully) {
    throw "내부 주소가 정상적으로 차단되지 않았습니다."
}

Write-Host "내부 주소 차단 성공"
Write-Host "모든 통합 테스트가 성공했습니다."