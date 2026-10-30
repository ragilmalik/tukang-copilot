"""Shopping helpers: turn a tool or part name into marketplace search links and a shareable list.

Pure functions, no network. Links open the Indonesian marketplaces' own search pages, so the user
compares real prices themselves (Tukang Copilot never buys anything)."""
from __future__ import annotations

from typing import Any
from urllib.parse import quote, quote_plus

MAX_NAME = 80


def clean(name: str) -> str:
    return " ".join(str(name).split())[:MAX_NAME]


def tokopedia_url(name: str) -> str:
    return "https://www.tokopedia.com/search?q=" + quote_plus(clean(name))


def shopee_url(name: str) -> str:
    return "https://shopee.co.id/search?keyword=" + quote_plus(clean(name))


def with_links(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Copy of tools/parts with `shop_url` (Tokopedia) and `shop_alt_url` (Shopee) added."""
    out: list[dict[str, Any]] = []
    for it in items:
        name = clean(it.get("name", ""))
        if not name:
            continue
        out.append({**it, "name": name, "shop_url": tokopedia_url(name), "shop_alt_url": shopee_url(name)})
    return out


def share_text(problem: str, tools: list[dict[str, Any]], parts: list[dict[str, Any]], lang: str = "id") -> str:
    """Plain-text shopping list for WhatsApp."""
    head = {"id": "Daftar belanja perbaikan", "jv": "Dhaptar blanja didandani", "en": "Repair shopping list"}.get(lang, "Repair shopping list")
    lines = [f"{head}: {clean(problem)}" if problem else head]
    for label, items in ((("Alat" if lang != "en" else "Tools"), tools), (("Suku cadang" if lang != "en" else "Parts"), parts)):
        if items:
            lines.append(f"{label}:")
            for it in items:
                price = int(it.get("est_price_idr") or 0)
                lines.append(f"- {clean(it.get('name', ''))}" + (f" (~Rp{price:,})".replace(",", ".") if price else ""))
    lines.append("Tukang Copilot")
    return "\n".join(lines)


def whatsapp_url(text: str) -> str:
    return "https://wa.me/?text=" + quote(text)
