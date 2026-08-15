package com.phishing.backend.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

@JsonIgnoreProperties(ignoreUnknown = true)
public record MultimodalResponse(
        @JsonProperty("analysis_id") String analysisId,
        String status,
        @JsonProperty("multimodal_result") Result multimodalResult,
        @JsonProperty("model_name") String modelName,
        @JsonProperty("prompt_version") String promptVersion
) {
    @JsonIgnoreProperties(ignoreUnknown = true)
    public record Result(
            @JsonProperty("multimodal_risk_score") Integer riskScore,
            @JsonProperty("risk_level") String riskLevel,
            @JsonProperty("is_financial_impersonation") boolean isFinancialImpersonation,
            @JsonProperty("impersonated_brand") String impersonatedBrand,
            @JsonProperty("brand_category") String brandCategory,
            @JsonProperty("attack_type") String attackType,
            @JsonProperty("detected_elements") List<String> detectedElements,
            List<Reason> reasons,
            Double confidence
    ) {
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public record Reason(String code, String description) {
    }
}
