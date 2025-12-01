from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db.session import get_session
from app.models.product import Product
from app.services.wix_client import WixClient
from app.services.catalog_normalizer import normalize_product

router = APIRouter(prefix="/wix", tags=["wix"])


@router.get("/debug-products")
def debug_wix_products():
    """
    Test : voir ce que Wix retourne et comment c’est normalisé.
    """
    client = WixClient()
    version, raw_products = client.query_products(limit=20)
    normalized = [normalize_product(p, version) for p in raw_products]

    return {
        "catalog_version": version,
        "count": len(normalized),
        "products": normalized,
    }


@router.post("/sync")
def sync_wix_to_luxura(db: Session = Depends(get_session)):
    """
    Sync complète des produits Wix vers la DB Luxura.
    """
    try:
        client = WixClient()
        version, raw_products = client.query_products(limit=500)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    synced = 0

    for wp in raw_products:
        data = normalize_product(wp, version)
        wix_id = data.get("wix_id")
        if not wix_id:
            continue

        stmt = select(Product).where(Product.wix_id == wix_id)
        existing = db.exec(stmt).first()

        if existing:
            # mise à jour
            for field, value in data.items():
                setattr(existing, field, value)
        else:
            # création
            db.add(Product(**data))
        synced += 1

    db.commit()
    return {"catalog_version": version, "synced": synced}
