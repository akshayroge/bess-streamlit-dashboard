import base64

from src.paths import ROOT, CSS_PATH


def load_css() -> str:
    if CSS_PATH.exists():
        return CSS_PATH.read_text(encoding="utf-8")
    return ""


def placeholder_svg(label: str) -> str:
    svg = f"""
    <svg xmlns="http://www.w3.org/2000/svg" width="360" height="160" viewBox="0 0 360 160">
      <rect width="360" height="160" rx="16" fill="#101c2f"/>
      <rect x="14" y="14" width="332" height="132" rx="12" fill="#07111f" stroke="#00d9ff" stroke-opacity="0.55"/>
      <text x="180" y="88" fill="#f4f8ff" font-size="20" font-weight="700" text-anchor="middle" font-family="Arial">{label}</text>
    </svg>
    """
    encoded = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
    return f"data:image/svg+xml;base64,{encoded}"


def asset_to_data_uri(path_text: str, label: str = "IMAGE") -> str:
    if not path_text:
        return placeholder_svg(label)

    path = ROOT / path_text

    if not path.exists():
        return placeholder_svg(label)

    suffix = path.suffix.lower()

    if suffix in [".jpg", ".jpeg"]:
        mime = "jpeg"
    elif suffix == ".png":
        mime = "png"
    elif suffix == ".webp":
        mime = "webp"
    elif suffix == ".svg":
        mime = "svg+xml"
    else:
        return placeholder_svg(label)

    encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:image/{mime};base64,{encoded}"
