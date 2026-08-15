package com.phishing.backend.service;

import com.phishing.backend.dto.AnalyzeRequest;
import com.phishing.backend.dto.SandboxResponse;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.time.Duration;

@Service
public class SandboxService {

    private final WebClient sandboxWebClient;

    public SandboxService(WebClient sandboxWebClient) {
        this.sandboxWebClient = sandboxWebClient;
    }

    public Mono<SandboxResponse> analyze(AnalyzeRequest request) {
        return sandboxWebClient.post()
                .uri("/analyze")
                .bodyValue(request)
                .retrieve()
                .bodyToMono(SandboxResponse.class)
                .timeout(Duration.ofSeconds(35));
    }
}