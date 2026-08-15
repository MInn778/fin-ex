package com.phishing.backend.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.phishing.backend.dto.AnalysisResult;
import com.phishing.backend.dto.AnalyzeRequest;
import com.phishing.backend.dto.DbApiSaveRequest;
import com.phishing.backend.dto.MlServiceResponse;
import com.phishing.backend.dto.SandboxResponse;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.time.Duration;

/**
 * 1차 ML(ml-service)로 위험도를 계산하고, 정밀 분석이 필요한 URL만
 * Sandbox에서 Screenshot/HTML을 추가로 수집한 뒤 db-api에 최종 결과를 저장한다.
 * multimodal-service는 아직 HTTP API가 없어 이 체인에서는 제외되어 있다.
 */
@Service
public class AnalysisOrchestrator {

    private final WebClient mlServiceWebClient;
    private final WebClient dbApiWebClient;
    private final SandboxService sandboxService;
    private final ObjectMapper objectMapper;

    public AnalysisOrchestrator(
            WebClient mlServiceWebClient,
            WebClient dbApiWebClient,
            SandboxService sandboxService,
            ObjectMapper objectMapper
    ) {
        this.mlServiceWebClient = mlServiceWebClient;
        this.dbApiWebClient = dbApiWebClient;
        this.sandboxService = sandboxService;
        this.objectMapper = objectMapper;
    }

    public Mono<AnalysisResult> analyze(AnalyzeRequest request) {
        return mlServiceWebClient.post()
                .uri("/v1/analyze")
                .bodyValue(request)
                .retrieve()
                .bodyToMono(MlServiceResponse.class)
                .timeout(Duration.ofSeconds(15))
                .flatMap(mlResult -> attachSandbox(request, mlResult))
                .flatMap(this::persist);
    }

    private Mono<CombinedResult> attachSandbox(AnalyzeRequest request, MlServiceResponse mlResult) {
        if (!mlResult.requiresDeepAnalysis()) {
            return Mono.just(new CombinedResult(mlResult, null, "not_required"));
        }

        return sandboxService.analyze(request)
                .map(sandbox -> new CombinedResult(mlResult, sandbox, null))
                .onErrorResume(error -> Mono.just(new CombinedResult(mlResult, null, error.getMessage())));
    }

    private Mono<AnalysisResult> persist(CombinedResult combined) {
        DbApiSaveRequest saveRequest = new DbApiSaveRequest(
                combined.ml.url(),
                combined.ml.riskScore(),
                writeJson(combined.ml),
                writeJson(sandboxSummary(combined)),
                writeJson(combined.ml.xaiReasons()),
                combined.ml.label()
        );

        return dbApiWebClient.post()
                .uri("/api/analyze")
                .bodyValue(saveRequest)
                .retrieve()
                .bodyToMono(AnalysisResult.class)
                .timeout(Duration.ofSeconds(10));
    }

    private SandboxSummary sandboxSummary(CombinedResult combined) {
        if (combined.sandbox == null) {
            return new SandboxSummary(false, null, null, combined.sandboxError);
        }
        return new SandboxSummary(
                true,
                combined.sandbox.htmlSizeBytes(),
                combined.sandbox.screenshotSizeBytes(),
                combined.sandbox.error()
        );
    }

    private String writeJson(Object value) {
        try {
            return objectMapper.writeValueAsString(value);
        } catch (Exception exception) {
            return "{}";
        }
    }

    private record CombinedResult(MlServiceResponse ml, SandboxResponse sandbox, String sandboxError) {
    }

    private record SandboxSummary(
            boolean collected,
            Integer htmlSizeBytes,
            Integer screenshotSizeBytes,
            String note
    ) {
    }
}
