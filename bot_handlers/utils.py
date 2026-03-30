def normalize_stored_path(p: str) -> str:
    return (p or "").replace("\\", "/")


def safe_path_component(text: str) -> str:
    bad = '<>:"/\\|?*'
    out = "".join("_" if c in bad else c for c in (text or "").strip())
    return " ".join(out.split())[:120] or "unknown"