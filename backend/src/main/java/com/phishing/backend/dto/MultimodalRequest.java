package com.phishing.backend.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public record MultimodalRequest(
        String url,
        @JsonProperty("final_url") String finalUrl,
        @JsonProperty("screenshot_base64") String screenshotBase64,
        String html
) {
}
