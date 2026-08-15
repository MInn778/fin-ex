package com.phishing.backend.dto;

import jakarta.validation.constraints.NotBlank;

public record AnalyzeRequest(
        @NotBlank(message = "url을 입력해주세요.")
        String url
) {
}