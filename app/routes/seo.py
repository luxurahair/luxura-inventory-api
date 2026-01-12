# app/routes/seo.py

import os
import re
import unicodedata
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db import get_session
from app.models.product import Product

router = APIRouter(prefix="/seo", tags=["seo"])


# ---------------------------
# Helpers texte
# ---------------------------
def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _clean(s: Any) -> str:
    return (str(s) if s is not None else "").strip()


def _truncate(s: str, max_len: int) -> str:
    s = (s or "").strip()
    if len(s) <= max_len:
        return s
    cut = s[:max_len].rsplit(" ", 1)[0].strip()
    return cut if cut else s[:max_len].strip()


def _strip_accents(s: str) -> str:
    # pour slugs propres (sans é/à/ç)
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _slugify(s: str) -> str:
    s = _strip_accents(_clean(s).lower())
    s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE)
    s = re.sub(r"[\s_-]+", "-", s)
    s = s.strip("-")
    return s[:80] or "produit"


def _split_parent_and_variant(name: str) -> Tuple[str, str]:
    """
    Ton prod.name Luxura est souvent: "Nom parent — 20\" 50 grammes"
    On split pour éviter les doublons SEO.
    """
    n = _clean(name)
    if "—" in n:
        left, right = n.split("—", 1)
        return left.strip(), right.strip()
    return n, ""


# ---------------------------
# Catégories (Wix collections)
# ---------------------------
_IGNORE_CATS = {"all products", "tous les produits", "all product", "toutes", "tous"}

def _categories(opts: Any) -> List[str]:
    if isinstance(opts, dict):
        cats = opts.get("categories") or []
        if isinstance(cats, list):
            return [str(c).strip() for c in cats if str(c).strip()]
    return []


def _best_category(opts: Any) -> str:
    """
    Choisit une catégorie utile SEO:
    - ignore All Products
    - privilégie Genius/Halo/Tape/i-Tip/Ponytail/Soins/Outils/Liquidation
    - sinon prend la catégorie la plus longue (souvent plus spécifique)
    """
    cats = _categories(opts)
    clean = [c for c in cats if c.strip().lower() not in _IGNORE_CATS]

    if not clean:
        return ""

    # priorités (tu peux en ajouter)
    priority = ["genius", "halo", "tape", "i-tip", "itip", "pony", "soins", "outils", "accessoires", "liquidation"]
    for key in priority:
        for c in clean:
            if key in c.lower():
                return c

    # sinon: la plus descriptive
    return sorted(clean, key=lambda x: len(x), reverse=True)[0]


def _seo_category_label(cat: str) -> str:
    c = (cat or "").strip()

    # raccourcis utiles (adaptés à ton Wix)
    if "genius" in c.lower():
        return "Genius"
    if "halo" in c.lower():
        return "Halo"
    if "tape" in c.lower():
        return "Tape-in"
    if "i-tip" in c.lower() or "itip" in c.lower():
        return "I-Tip"
    if "pony" in c.lower():
        return "Ponytail"

    # sinon, on coupe si trop long
    return c[:30].strip()


def _choice_text(opts: Any) -> str:
    """
    Valeur variante (ex: Longeur = 20" 50 grammes)
    """
    if isinstance(opts, dict):
        choices = opts.get("choices") or {}
        if isinstance(choices, dict):
            for k in ("Longeur", "Longueur"):
                if k in choices and choices[k]:
                    return str(choices[k]).strip()
            for _, v in choices.items():
                if v:
                    return str(v).strip()
    return ""


# ---------------------------
# Génération SEO (FR/EN)
# ---------------------------

def _build_seo_parent_fr(parent_name: str, category: str) -> Dict[str, str]:
    cat = f"{category} – " if category else ""
    title = _truncate(f"{cat}{parent_name} | Luxura Distribution", 60)
    meta = _truncate(
        f"{parent_name}. Extensions capillaires haut de gamme pour salons. Livraison rapide au Québec et au Canada.",
        160,
    )
    slug = _slugify(f"{category} {parent_name}".strip())
    return {"title": title, "meta": meta, "slug": slug}


def _build_seo_parent_en(parent_name: str, category: str) -> Dict[str, str]:
    cat = f"{category} – " if category else ""
    title = _truncate(f"{cat}{parent_name} | Luxura Distribution", 60)
    meta = _truncate(
        f"{parent_name}. Premium professional hair extensions for salons. Fast shipping in Quebec & Canada.",
        160,
    )
    slug = _slugify(f"{category} {parent_name}".strip())
    return {"title": title, "meta": meta, "slug": slug}


def _build_seo_variant_fr(parent_name: str, choice_txt: str, category: str) -> Dict[str, str]:
    extra = f" – {choice_txt}" if choice_txt else ""
    cat = f"{category} – " if category else ""
    title = _truncate(f"{cat}{parent_name}{extra} | Luxura", 60)
    meta = _truncate(
        f"{parent_name}{extra}. Qualité salon, rendu naturel. Stock réel et livraison rapide au Québec et au Canada.",
        160,
    )
    slug = _slugify(f"{category} {parent_name} {choice_txt}".strip())
    return {"title": title, "meta": meta, "slug": slug}


def _build_seo_variant_en(parent_name: str, choice_txt: str, category: str) -> Dict[str, str]:
    extra = f" – {choice_txt}" if choice_txt else ""
    cat = f"{category} – " if category else ""
    title = _truncate(f"{cat}{parent_name}{extra} | Luxura", 60)
    meta = _truncate(
        f"{parent_name}{extra}. Professional salon-grade hair extensions. Live stock and fast shipping in Quebec & Canada.",
        160,
    )
    slug = _slugify(f"{category} {parent_name} {choice_txt}".strip())
    return {"title": title, "meta": meta, "slug": slug}


# ALT images (FR/EN) — utile pour ton étape 2
def _build_alt_fr(category: str, parent_name: str, choice_txt: str) -> str:
    cat = category if category else "Extensions"
    extra = f" {choice_txt}" if choice_txt else ""
    return _truncate(f"{cat} professionnelles – {parent_name}{extra} – Luxura Distribution (Québec)", 120)


def _build_alt_en(category: str, parent_name: str, choice_txt: str) -> str:
    cat = category if category else "Hair extensions"
    extra = f" {choice_txt}" if choice_txt else ""
    return _truncate(f"Professional {cat} – {parent_name}{extra} – Luxura Distribution (Canada)", 120)


# ---------------------------
# Endpoints
# ---------------------------
@router.post("/preview")
def seo_preview(
    limit: int = 50,
    category: Optional[str] = None,      # filtre optionnel
    only_missing: bool = False,
    session: Session = Depends(get_session),
) -> Dict[str, Any]:
    """
    Calcule SEO parent + variant (FR+EN) sans écrire.
    """
    q = select(Product).where(Product.wix_id.is_not(None))
    products = session.exec(q).all()

    # filtre par catégorie (si demandé)
    if category:
        want = category.strip().lower()
        products = [
            p for p in products
            if isinstance(p.options, dict)
            and any(str(c).strip().lower() == want for c in (_categories(p.options)))
        ]

    products = products[: max(1, int(limit))]

    changes: List[Dict[str, Any]] = []
    for p in products:
        opts = p.options if isinstance(p.options, dict) else {}

        best_cat = _seo_category_label(_best_category(opts))
        parent_name, name_variant_part = _split_parent_and_variant(p.name or "")
        choice_txt = _choice_text(opts) or name_variant_part

        proposed_parent_fr = _build_seo_parent_fr(parent_name, best_cat)
        proposed_parent_en = _build_seo_parent_en(parent_name, best_cat)
        proposed_variant_fr = _build_seo_variant_fr(parent_name, choice_txt, best_cat)
        proposed_variant_en = _build_seo_variant_en(parent_name, choice_txt, best_cat)

        proposed_variant_fr["alt"] = _build_alt_fr(best_cat, parent_name, choice_txt)
        proposed_variant_en["alt"] = _build_alt_en(best_cat, parent_name, choice_txt)

        current_parent = (opts.get("seo_parent") or {}) if isinstance(opts, dict) else {}
        current_variant = (opts.get("seo_variant") or {}) if isinstance(opts, dict) else {}

        if only_missing and current_parent and current_variant:
            continue

        changes.append(
            {
                "product_id": p.id,
                "wix_id": p.wix_id,
                "sku": p.sku,
                "name": p.name,
                "category_used": best_cat,
                "choice": choice_txt,
                "current": {"seo_parent": current_parent, "seo_variant": current_variant},
                "proposed": {
                    "seo_parent_fr": proposed_parent_fr,
                    "seo_parent_en": proposed_parent_en,
                    "seo_variant_fr": proposed_variant_fr,
                    "seo_variant_en": proposed_variant_en,
                },
            }
        )

    return {"ok": True, "count": len(changes), "changes": changes}


@router.post("/apply")
def seo_apply(
    product_ids: List[int],
    confirm: bool = False,
    secret: Optional[str] = None,
    session: Session = Depends(get_session),
) -> Dict[str, Any]:
    """
    Écrit SEO dans Luxura (options.seo_parent/seo_variant).
    Push vers Wix plus tard via OAuth/Velo.
    """
    if not confirm:
        raise HTTPException(status_code=400, detail="confirm=true requis")

    expected = os.getenv("SEO_SECRET") or ""
    if expected and secret != expected:
        raise HTTPException(status_code=403, detail="SEO_SECRET invalide")

    updated = 0
    now_iso = _now_utc().isoformat().replace("+00:00", "Z")

    for pid in product_ids:
        prod = session.get(Product, pid)
        if not prod:
            continue

        opts = prod.options if isinstance(prod.options, dict) else {}

        best_cat = _seo_category_label(_best_category(opts))
        parent_name, name_variant_part = _split_parent_and_variant(prod.name or "")
        choice_txt = _choice_text(opts) or name_variant_part

        seo_parent_fr = _build_seo_parent_fr(parent_name, best_cat)
        seo_parent_en = _build_seo_parent_en(parent_name, best_cat)

        seo_variant_fr = _build_seo_variant_fr(parent_name, choice_txt, best_cat)
        seo_variant_en = _build_seo_variant_en(parent_name, choice_txt, best_cat)

        seo_variant_fr["alt"] = _build_alt_fr(best_cat, parent_name, choice_txt)
        seo_variant_en["alt"] = _build_alt_en(best_cat, parent_name, choice_txt)

        # Stockage 4A dans Luxura
        opts["seo_parent"] = {
            "fr": seo_parent_fr,
            "en": seo_parent_en,
            "category_used": best_cat,
            "updated_at": now_iso,
        }
        opts["seo_variant"] = {
            "fr": seo_variant_fr,
            "en": seo_variant_en,
            "category_used": best_cat,
            "updated_at": now_iso,
        }

        prod.options = opts
        updated += 1

    session.commit()

    return {
        "ok": True,
        "updated": updated,
        "note": "SEO stocké dans Luxura (options.seo_parent/seo_variant). Push Wix nécessitera OAuth/Velo.",
    }
