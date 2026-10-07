from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

import imagehash
from PIL import Image

BRANDS_DIR = Path(__file__).parents[2] / "brands"


@lru_cache(maxsize=1)
def _brand_hashes() -> dict[str, list[imagehash.ImageHash]]:
    hashes: dict[str, list[imagehash.ImageHash]] = {}
    if not BRANDS_DIR.exists():
        return hashes
    for brand_dir in BRANDS_DIR.iterdir():
        if brand_dir.is_dir():
            for image_path in brand_dir.glob("*.png"):
                with Image.open(image_path) as image:
                    hashes.setdefault(brand_dir.name, []).append(
                        imagehash.phash(image.convert("RGB"))
                    )
    return hashes


def perceptual_hash(path: str | Path) -> str:
    with Image.open(path) as image:
        return str(imagehash.phash(image.convert("RGB")))


def phash_match(
    path: str | Path, threshold: int = 12, brand_hint: str | None = None
) -> dict:
    try:
        with Image.open(path) as image:
            suspect = imagehash.phash(image.convert("RGB"))
    except (OSError, ValueError) as error:
        return {"matched": False, "brand": None, "distance": None, "error": str(error)}

    best: tuple[str, int] | None = None
    for brand, references in _brand_hashes().items():
        for reference in references:
            distance = suspect - reference
            if best is None or distance < best[1]:
                best = (brand, distance)
    result = {
        "matched": bool(best and best[1] <= threshold),
        "brand": best[0] if best else None,
        "distance": best[1] if best else None,
    }
    if brand_hint:
        result["brand"] = brand_hint
    return result


def official_brand_for_url(url: str) -> str | None:
    hostname = (urlparse(url).hostname or "").lower()
    official_domains = {
        "paytm.com": "paytm",
        "phonepe.com": "phonepe",
        "google.com": "gpay",
        "sbi.co.in": "sbi",
    }
    for domain, brand in official_domains.items():
        if hostname == domain or hostname.endswith(f".{domain}"):
            return brand
    return None
