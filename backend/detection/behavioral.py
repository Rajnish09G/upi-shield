from dataclasses import dataclass
from urllib.parse import urlparse

from bs4 import BeautifulSoup


@dataclass(frozen=True)
class BehavioralSignals:
    external_form_action: bool = False
    suspicious_redirect: bool = False
    brand_keyword_count: int = 0
    sensitive_inputs: tuple[str, ...] = ()
    external_form_posts: tuple[str, ...] = ()


def inspect_dom(
    html: str, brand_keywords: list[str], page_url: str | None = None
) -> BehavioralSignals:
    soup = BeautifulSoup(html, "html.parser")
    lowered = soup.get_text(" ", strip=True).lower()
    sensitive_names = {"password", "pin", "otp", "cvv", "card", "upi", "vpa"}
    inputs = [
        str(field.get("name", "")).lower()
        for field in soup.find_all("input")
        if field.get("name")
    ]
    origin = urlparse(page_url).netloc if page_url else None
    external_posts = tuple(
        action
        for form in soup.find_all("form")
        for action in [str(form.get("action", "")).strip()]
        if action.startswith("http")
        and origin
        and urlparse(action).netloc != origin
    )
    return BehavioralSignals(
        external_form_action=bool(external_posts),
        suspicious_redirect="window.location" in html.lower(),
        brand_keyword_count=sum(lowered.count(word.lower()) for word in brand_keywords),
        sensitive_inputs=tuple(
            name for name in inputs if any(term in name for term in sensitive_names)
        ),
        external_form_posts=external_posts,
    )
