const express = require("express");
const { chromium } = require("playwright");
const { validateUrl } = require("./urlValidator");

const app = express();
const PORT = Number(process.env.PORT) || 3001;

const MAX_HTML_BYTES = 2 * 1024 * 1024;
const MAX_SCREENSHOT_BYTES = 10 * 1024 * 1024;
const ANALYSIS_TIMEOUT_MS = 30000;

app.use(express.json({ limit: "1mb" }));

app.get("/health", (req, res) => {
  res.json({
    status: "UP",
    service: "phishing-sandbox",
  });
});

app.post("/analyze", async (req, res) => {
  const { url } = req.body;

  if (!url) {
    return res.status(400).json({
      code: "URL_REQUIRED",
      message: "url을 입력해주세요.",
    });
  }

  let validatedUrl;

  try {
    validatedUrl = await validateUrl(url);
  } catch (error) {
    return res.status(400).json({
      code: error.code || "URL_VALIDATION_FAILED",
      message: error.message,
    });
  }

  let browser;
  let blockedRequestError = null;
  let analysisTimedOut = false;
  let analysisTimer = null;
  const startedAt = Date.now();

  try {
    analysisTimer = setTimeout(() => {
      analysisTimedOut = true;

      if (browser) {
        browser.close().catch(() => {});
      }
    }, ANALYSIS_TIMEOUT_MS);
    browser = await chromium.launch({
      headless: true,
    });

    const context = await browser.newContext({
      viewport: {
        width: 1440,
        height: 900,
      },
      permissions: [],
      acceptDownloads: false,
      serviceWorkers: "block",
    });

    const validatedHosts = new Set();

    await context.route("**/*", async (route) => {
      const requestUrl = route.request().url();

      if (!requestUrl.startsWith("http://") && !requestUrl.startsWith("https://")) {
        return route.continue();
      }

      try {
        const hostname = new URL(requestUrl).hostname;

        if (!validatedHosts.has(hostname)) {
          await validateUrl(requestUrl);
          validatedHosts.add(hostname);
        }

        return route.continue();
      } catch (error) {
        blockedRequestError = error;
        console.warn("차단된 요청:", requestUrl);
        return route.abort("blockedbyclient");
      }
    });

    const page = await context.newPage();

    page.on("popup", async (popup) => {
      console.warn("팝업 차단:", popup.url());
      await popup.close().catch(() => {});
    });

    page.on("download", async (download) => {
      console.warn("다운로드 차단:", download.suggestedFilename());
      await download.cancel().catch(() => {});
    });

    page.on("dialog", async (dialog) => {
      console.warn("대화상자 차단:", dialog.type());
      await dialog.dismiss().catch(() => {});
    });

    context.on("page", async (newPage) => {
      if (newPage !== page) {
        console.warn("새 탭 차단:", newPage.url());
        await newPage.close().catch(() => {});
      }
    });

    const response = await page.goto(validatedUrl, {
      waitUntil: "domcontentloaded",
      timeout: 15000,
    });

    const html = await page.content();

    const htmlSize = Buffer.byteLength(html, "utf8");

    if (htmlSize > MAX_HTML_BYTES) {
      const error = new Error("HTML 크기가 2MB를 초과했습니다.");
      error.code = "HTML_TOO_LARGE";
      throw error;
    }

    const screenshot = await page.screenshot({
      fullPage: true,
      type: "png",
    });

    if (screenshot.length > MAX_SCREENSHOT_BYTES) {
      const error = new Error("스크린샷 크기가 10MB를 초과했습니다.");
      error.code = "SCREENSHOT_TOO_LARGE";
      throw error;
    }

    return res.json({
      requestedUrl: validatedUrl,
      finalUrl: page.url(),
      statusCode: response?.status() ?? null,
      title: await page.title(),
      html,
      htmlSizeBytes: htmlSize,
      screenshotBase64: screenshot.toString("base64"),
      screenshotSizeBytes: screenshot.length,
      loadTimeMs: Date.now() - startedAt,
      error: null,
    });
  } catch (error) {
  if (analysisTimedOut) {
    return res.status(504).json({
      code: "ANALYSIS_TIMEOUT",
      message: "전체 분석 제한 시간 30초를 초과했습니다.",
    });
  }

  if (blockedRequestError) {
    return res.status(400).json({
      code: blockedRequestError.code || "BLOCKED_NETWORK_REQUEST",
      message: blockedRequestError.message,
    });
  }

  if (error.code === "HTML_TOO_LARGE" || error.code === "SCREENSHOT_TOO_LARGE") {
    return res.status(413).json({
      code: error.code,
      message: error.message,
    });
  }

  const isTimeout = error.name === "TimeoutError";

  return res.status(isTimeout ? 504 : 500).json({
    code: isTimeout ? "PAGE_LOAD_TIMEOUT" : "SANDBOX_ERROR",
    message: error.message,
  });
} finally {
    if (analysisTimer) {
      clearTimeout(analysisTimer);

    }
    if (browser) {
      await browser.close().catch(() => {});
    }
  }
});

app.listen(PORT, "0.0.0.0", () => {
  console.log(`Sandbox API 실행: http://localhost:${PORT}`);
});
