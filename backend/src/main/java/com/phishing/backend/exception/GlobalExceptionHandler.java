package com.phishing.backend.exception;

import com.phishing.backend.dto.ApiError;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.support.WebExchangeBindException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.reactive.function.client.WebClientRequestException;
import org.springframework.web.reactive.function.client.WebClientResponseException;

import java.util.concurrent.TimeoutException;

@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(WebClientResponseException.class)
    public ResponseEntity<String> handleSandboxResponse(
            WebClientResponseException exception
    ) {
        String responseBody = exception.getResponseBodyAsString();

        if (responseBody == null || responseBody.isBlank()) {
            responseBody = """
                    {
                      "code": "SANDBOX_ERROR",
                      "message": "Sandbox가 오류를 반환했습니다."
                    }
                    """;
        }

        return ResponseEntity
                .status(exception.getStatusCode())
                .contentType(MediaType.APPLICATION_JSON)
                .body(responseBody);
    }

    @ExceptionHandler(WebClientRequestException.class)
    public ResponseEntity<ApiError> handleSandboxConnection(
            WebClientRequestException exception
    ) {
        return ResponseEntity
                .status(HttpStatus.BAD_GATEWAY)
                .body(new ApiError(
                        "SANDBOX_UNAVAILABLE",
                        "Sandbox 서버에 연결할 수 없습니다."
                ));
    }

    @ExceptionHandler(TimeoutException.class)
    public ResponseEntity<ApiError> handleTimeout(
            TimeoutException exception
    ) {
        return ResponseEntity
                .status(HttpStatus.GATEWAY_TIMEOUT)
                .body(new ApiError(
                        "SANDBOX_TIMEOUT",
                        "Sandbox 응답 대기 시간을 초과했습니다."
                ));
    }

    @ExceptionHandler(WebExchangeBindException.class)
    public ResponseEntity<ApiError> handleValidation(
            WebExchangeBindException exception
    ) {
        String message = exception.getFieldErrors().isEmpty()
                ? "요청값이 올바르지 않습니다."
                : exception.getFieldErrors().getFirst().getDefaultMessage();

        return ResponseEntity
                .badRequest()
                .body(new ApiError(
                        "INVALID_REQUEST",
                        message
                ));
    }
}