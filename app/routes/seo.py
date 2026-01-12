# app/routes/seo.py

import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db import get_session
from app.models.product import Product

router = APIRouter(prefix="/seo", tags=["seo"])


def _slugify(s: str) -> str:
    s = (s or "").lower().strip()
    s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE)
    s = re.sub(r"[\s_-]+", "-", s)
    s = s.strip("-")
    return s[:80] or "produit"


def _first_category(opts: Any) -> str:
    if isinstance(opts, dict):
        cats = opts.get("categories") or []
        if isinstance(cats, list) and cats:
            return str(cats[0])
    return ""


def _choice_text(opts: Any) -> str:
    # ex: "20\" 50 grammes" (Longeur)
    if isinstance(opts, dict):
        choices = opts.get("choices") or {}
        if isinstance(choices, dict):
            # priorité Longeur/Longueur
            for k in ("Longeur", "Longueur"):
                if k in choices and choices[k]:
                    return str(choices[k])
            # sinon premier choix
            for _, v in choices.items():
                if v:
                    return str(v)
    return ""


def _build_seo_parent(prod_name: str, category: str) -> Dict[str, str]:
    # SEO parent = page produit (Google)
    cat = f"{category} " if category else ""
    title = f"{cat}{prod_name} | Luxura Distribution".strip()
    meta = f"{prod_name}. Extensions capillaires haut de gamme. Livraison rapide au Québec. Qualité salon.".strip()
    slug = _slugify(f"{cat}{prod_name}")
    return {"title": title[:60], "meta": meta[:160], "slug": slug}


def _build_seo_variant(prod_name: str, choice_txt: str, category: str) -> Dict[str, str]:
    # SEO variante = surtout pour Luxura + export + descriptions (pas forcément une page Wix)
    extra = f" – {choice_txt}" if choice_txt else ""
    cat = f"{category} " if category else ""
    title = f"{cat}{prod_name}{extra} | Luxura".strip()
    meta = f"{prod_name}{extra}. Extensions capillaires haut de gamme. Stock réel et livraison rapide.".strip()
    slug = _slugify(f"{cat}{prod_name}-{choice_txt}")
    return {"title": title[:60], "meta": meta[:160], "slug": slug}


@router.post("/preview")
def seo_preview(
    limit: int = 50,
    category: Optional[str] = None,
    only_missing: bool = False,
    session: Session = Depends(get_session),
) -> Dict[str, Any]:
    """
    Calcule SEO parent + variant sans écrire.
    """
    q = select(Product).where(Product.wix_id.is_not(None))
    products = session.exec(q).all()

    # filtre (simple) par catégorie si demandé
    if category:
        want = category.strip().lower()
        products = [
            p for p in products
            if isinstance(p.options, dict)
            and any(str(c).strip().lower() == want for c in (p.options.get("categories") or []))
        ]

    # limiter
    products = products[: max(1, int(limit))]

    changes: List[Dict[str, Any]] = []
    for p in products:
        opts = p.options if isinstance(p.options, dict) else {}
        cat0 = _first_category(opts)
        choice_txt = _choice_text(opts)

        seo_parent = _build_seo_parent(p.name or "", cat0)
        seo_variant = _build_seo_variant(p.name or "", choice_txt, cat0)

        current_parent = (opts.get("seo_parent") if isinstance(opts, dict) else None) or {}
        current_variant = (opts.get("seo_variant") if isinstance(opts, dict) else None) or {}

        # only_missing = propose seulement si absent
        if only_missing and current_parent and current_variant:
            continue

        changes.append({
            "product_id": p.id,
            "wix_id": p.wix_id,
            "sku": p.sku,
            "name": p.name,
            "category": cat0,
            "choice": choice_txt,
            "current": {"seo_parent": current_parent, "seo_variant": current_variant},
            "proposed": {"seo_parent": seo_parent, "seo_variant": seo_variant},
        })

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
    Pousser vers Wix nécessite OAuth / Velo (pas inclus ici).
    """
    if not confirm:
        raise HTTPException(status_code=400, detail="confirm=true requis")
    expected = os.getenv("SEO_SECRET") or ""
    if expected and secret != expected:
        raise HTTPException(status_code=403, detail="SEO_SECRET invalide")

    updated = 0
    for pid in product_ids:
        prod = session.get(Product, pid)
        if not prod:
            continue

        opts = prod.options if isinstance(prod.options, dict) else {}
        cat0 = _first_category(opts)
        choice_txt = _choice_text(opts)

        seo_parent = _build_seo_parent(prod.name or "", cat0)
        seo_variant = _build_seo_variant(prod.name or "", choice_txt, cat0)

        opts["seo_parent"] = {**seo_parent, "updated_at": datetime.utcnow().isoformat() + "Z"}
        opts["seo_variant"] = {**seo_variant, "updated_at": datetime.utcnow().isoformat() + "Z"}

        prod.options = opts
        updated += 1

    session.commit()

    return {
        "ok": True,
        "updated": updated,
        "note": "SEO stocké dans Luxura. Push vers Wix nécessite OAuth/Velo (Manage Products).",
    }
