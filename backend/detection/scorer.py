from .behavioral import BehavioralSignals
from .behavioral import inspect_dom
from .visual import official_brand_for_url, phash_match


def combine_signals(visual_similarity: float, behavioral: BehavioralSignals) -> float:
    suspicious_signal = (
        behavioral.external_form_action
        or behavioral.suspicious_redirect
        or bool(behavioral.sensitive_inputs)
    )
    behavioral_score = (
        (int(behavioral.external_form_action) * 0.4)
        + (int(behavioral.suspicious_redirect) * 0.35)
        + (int(bool(behavioral.sensitive_inputs)) * 0.2)
        + (int(suspicious_signal and behavioral.brand_keyword_count > 0) * 0.05)
    )
    return round(min(1.0, (visual_similarity * 0.6) + (behavioral_score * 0.4)), 4)


def score(
    url: str,
    screenshot: str,
    dom: str,
    brand_keywords: list[str],
    phishing_threshold: float = 0.6,
    suspicious_threshold: float = 0.35,
) -> dict:
    official_brand = official_brand_for_url(url)
    visual = phash_match(screenshot, brand_hint=official_brand)
    with open(dom, encoding="utf-8", errors="ignore") as stream:
        behavioral = inspect_dom(stream.read(), brand_keywords, url)
    similarity = (
        max(0.0, 1.0 - visual["distance"] / 64)
        if visual["distance"] is not None
        else 0.0
    )
    suspicious_behavior = (
        behavioral.external_form_action
        or behavioral.suspicious_redirect
        or bool(behavioral.sensitive_inputs)
    )
    final_score = combine_signals(similarity, behavioral)
    if official_brand and not suspicious_behavior:
        final_score = min(final_score, 0.3)
    verdict = (
        "phishing" if final_score >= phishing_threshold
        else "suspicious" if final_score >= suspicious_threshold
        else "benign"
    )
    return {
        "url": url,
        "brand": visual["brand"],
        "phash_distance": visual["distance"],
        "behavioral": {
            "external_form_posts": behavioral.external_form_posts,
            "sensitive_inputs": behavioral.sensitive_inputs,
            "brand_keyword_count": behavioral.brand_keyword_count,
        },
        "score": final_score,
        "verdict": verdict,
    }
