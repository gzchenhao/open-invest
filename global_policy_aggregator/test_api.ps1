# OpenInvest API Test Script
# Usage: powershell -ExecutionPolicy Bypass -File test_api.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "OpenInvest API Test Suite" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://localhost:8017"

# Test 1: Stats API
Write-Host "[Test 1] GET /api/stats" -ForegroundColor Yellow
try {
    $stats = Invoke-RestMethod -Uri "$baseUrl/api/stats" -Method GET
    Write-Host "  Total Policies: $($stats.total_policies)" -ForegroundColor Green
    Write-Host "  Regions: $($stats.regions_count)" -ForegroundColor Green
    Write-Host "  Industries: $($stats.industries_count)" -ForegroundColor Green
    Write-Host "  [PASS]" -ForegroundColor Green
} catch {
    Write-Host "  [FAIL] $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 2: Search API - Search for "AI"
Write-Host "[Test 2] POST /api/search (keywords=AI)" -ForegroundColor Yellow
try {
    $body = @{keywords="AI"; limit=10} | ConvertTo-Json
    $result = Invoke-RestMethod -Uri "$baseUrl/api/search" -Method POST -Body $body -ContentType "application/json"
    Write-Host "  Results: $($result.count)" -ForegroundColor Green
    if ($result.count -gt 0) {
        Write-Host "  First: $($result.policies[0].title)" -ForegroundColor Green
    }
    Write-Host "  [PASS]" -ForegroundColor Green
} catch {
    Write-Host "  [FAIL] $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 3: Search API - Search for "Beijing"
Write-Host "[Test 3] POST /api/search (keywords=Beijing)" -ForegroundColor Yellow
try {
    $body = @{keywords="Beijing"; limit=10} | ConvertTo-Json
    $result = Invoke-RestMethod -Uri "$baseUrl/api/search" -Method POST -Body $body -ContentType "application/json"
    Write-Host "  Results: $($result.count)" -ForegroundColor Green
    Write-Host "  [PASS]" -ForegroundColor Green
} catch {
    Write-Host "  [FAIL] $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 4: Empty search (should return all)
Write-Host "[Test 4] POST /api/search (keywords=empty)" -ForegroundColor Yellow
try {
    $body = @{keywords=""; limit=100} | ConvertTo-Json
    $result = Invoke-RestMethod -Uri "$baseUrl/api/search" -Method POST -Body $body -ContentType "application/json"
    Write-Host "  Results: $($result.count)" -ForegroundColor Green
    Write-Host "  [PASS]" -ForegroundColor Green
} catch {
    Write-Host "  [FAIL] $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 5: PDF Download
Write-Host "[Test 5] GET /api/policy/1/pdf" -ForegroundColor Yellow
try {
    $pdfPath = "test_policy_download.pdf"
    Invoke-WebRequest -Uri "$baseUrl/api/policy/1/pdf" -OutFile $pdfPath
    $fileSize = (Get-Item $pdfPath).Length
    Write-Host "  Downloaded: $fileSize bytes" -ForegroundColor Green
    Remove-Item $pdfPath -ErrorAction SilentlyContinue
    Write-Host "  [PASS]" -ForegroundColor Green
} catch {
    Write-Host "  [FAIL] $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "All tests completed!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
