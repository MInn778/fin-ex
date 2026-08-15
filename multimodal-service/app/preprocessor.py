from bs4 import BeautifulSoup


MAX_TEXT_LENGTH = 5000
MAX_HTML_LENGTH = 10000


def preprocess_page_text(page_text: str) -> str:
    if not page_text:
        return ""

    page_text = page_text.strip()

    if len(page_text) > MAX_TEXT_LENGTH:
        page_text = page_text[:MAX_TEXT_LENGTH]

    return page_text


def preprocess_html(html: str) -> str:
    if not html:
        return ""

    soup = BeautifulSoup(html, "html.parser")

    # 분석에 불필요한 요소 제거
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    cleaned_html = str(soup)

    if len(cleaned_html) > MAX_HTML_LENGTH:
        cleaned_html = cleaned_html[:MAX_HTML_LENGTH]

    return cleaned_html


def preprocess_input(input_data: dict) -> dict:
    processed_data = input_data.copy()

    processed_data["page_text"] = preprocess_page_text(
        input_data.get("page_text", "")
    )

    processed_data["html"] = preprocess_html(
        input_data.get("html", "")
    )

    return processed_data