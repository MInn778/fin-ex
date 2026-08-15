package com.phishing.backend.controller;

import com.phishing.backend.dto.AnalyzeRequest;
import com.phishing.backend.dto.SandboxResponse;
import com.phishing.backend.service.SandboxService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

@RestController
@RequestMapping("/api/v1/url-analysis")
public class UrlAnalysisController {

    private final SandboxService sandboxService;

    public UrlAnalysisController(SandboxService sandboxService) {
        this.sandboxService = sandboxService;
    }

    @PostMapping
    public Mono<SandboxResponse> analyze(
            @Valid @RequestBody AnalyzeRequest request
    ) {
        return sandboxService.analyze(request);
    }
}