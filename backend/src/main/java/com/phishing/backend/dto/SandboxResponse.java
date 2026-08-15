package com.phishing.backend.dto;

public record SandboxResponse(
        String requestedUrl,
        String finalUrl,
        Integer statusCode,
        String title,
        String html,
        Integer htmlSizeBytes,
        String screenshotBase64,
        Integer screenshotSizeBytes,
        Long loadTimeMs,
        String error
) {
}