from fastapi import FastAPI, APIRouter, HTTPException, Response, Request, Depends
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import httpx

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection for local data (auth, cart, etc.)
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Luxura Inventory API (Render)
LUXURA_API_URL = "https://luxura-inventory-api.onrender.com"

# Create the main app
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== MODELS ====================

class User(BaseModel):
    user_id: str
    email: str
    name: str
    picture: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserSession(BaseModel):
    session_token: str
    user_id: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CartItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    product_id: int  # Now using Luxura API product ID
    quantity: int = 1
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CartItemCreate(BaseModel):
    product_id: int
    quantity: int = 1

class CartItemUpdate(BaseModel):
    quantity: int

class BlogPost(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str
    excerpt: str
    image: Optional[str] = None
    author: str = "Luxura Distribution"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Salon(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    address: str
    city: str
    phone: Optional[str] = None
    website: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class Category(BaseModel):
    id: str
    name: str
    description: str
    image: Optional[str] = None
    wix_url: Optional[str] = None
    order: int = 0

# ==================== HELPER: Detect category from product name ====================

def detect_category(name: str) -> str:
    """Detect product category from name"""
    name_lower = name.lower()
    if 'genius' in name_lower or 'trame invisible' in name_lower or 'vivian' in name_lower:
        return 'genius'
    elif 'halo' in name_lower or 'everly' in name_lower:
        return 'halo'
    elif 'bande' in name_lower or 'tape' in name_lower or 'aurora' in name_lower or 'adhésive' in name_lower:
        return 'tape'
    elif 'i-tip' in name_lower or 'itip' in name_lower or 'eleanor' in name_lower:
        return 'i-tip'
    else:
        return 'essentiels'

def get_category_image(category: str) -> str:
    """Get default placeholder image for category - using smaller square images with Wix resizing"""
    # Using Wix image transformation to force 300x300 square images
    category_images = {
        "genius": "https://static.wixstatic.com/media/f1b961_0765bab9e407403289c86e98fcb27476~mv2.png/v1/crop/x_0,y_100,w_1000,h_1000/fill/w_300,h_300,al_c,q_85/genius.webp",
        "halo": "https://static.wixstatic.com/media/f1b961_42148bb43bbe484f9ca8f1127a4d30e4~mv2.png/v1/crop/x_0,y_100,w_1000,h_1000/fill/w_300,h_300,al_c,q_85/halo.webp",
        "tape": "https://static.wixstatic.com/media/f1b961_8bed6fa0069a41c3971d7dcb51ab1cec~mv2.png/v1/fill/w_300,h_300,al_c,q_85/tape.webp",
        "i-tip": "https://static.wixstatic.com/media/f1b961_0d440382da1f450da579fd73c14daf88~mv2.png/v1/crop/x_0,y_100,w_1000,h_1000/fill/w_300,h_300,al_c,q_85/itip.webp",
        "essentiels": "https://static.wixstatic.com/media/de6cdb_1977c4f9e78645a38131eaa992c478ce~mv2.jpg/v1/fill/w_300,h_300,al_c,q_85/essentiels.webp"
    }
    return category_images.get(category, "https://static.wixstatic.com/media/f1b961_0765bab9e407403289c86e98fcb27476~mv2.png/v1/crop/x_0,y_100,w_1000,h_1000/fill/w_300,h_300,al_c,q_85/default.webp")

def extract_image_from_options(options: Dict[str, Any]) -> Optional[str]:
    """Extract first image URL from product options"""
    if not options:
        return None
    
    images = options.get('images')
    if images and isinstance(images, list) and len(images) > 0:
        # Wix media format
        first_img = images[0]
        if isinstance(first_img, dict):
            url = first_img.get('url') or first_img.get('src')
            if url:
                return url
        elif isinstance(first_img, str):
            return first_img
    
    # Try mainMedia
    main_media = images.get('mainMedia') if isinstance(images, dict) else None
    if main_media:
        if isinstance(main_media, dict):
            return main_media.get('url') or main_media.get('src')
    
    return None

# ==================== AUTH HELPERS ====================

async def get_current_user(request: Request) -> Optional[User]:
    """Get current user from session token in cookie or Authorization header"""
    session_token = request.cookies.get("session_token")
    
    if not session_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_token = auth_header[7:]
    
    if not session_token:
        return None
    
    session_doc = await db.user_sessions.find_one(
        {"session_token": session_token},
        {"_id": 0}
    )
    
    if not session_doc:
        return None
    
    expires_at = session_doc["expires_at"]
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        return None
    
    user_doc = await db.users.find_one(
        {"user_id": session_doc["user_id"]},
        {"_id": 0}
    )
    
    if not user_doc:
        return None
    
    return User(**user_doc)

async def require_auth(request: Request) -> User:
    """Require authenticated user"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

# ==================== AUTH ENDPOINTS ====================

@api_router.post("/auth/session")
async def exchange_session(request: Request, response: Response):
    """Exchange session_id for session_token"""
    body = await request.json()
    session_id = body.get("session_id")
    
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")
    
    # Call Emergent Auth to get user data
    async with httpx.AsyncClient() as client:
        auth_response = await client.get(
            "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
            headers={"X-Session-ID": session_id}
        )
    
    if auth_response.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    auth_data = auth_response.json()
    email = auth_data.get("email")
    name = auth_data.get("name")
    picture = auth_data.get("picture")
    session_token = auth_data.get("session_token")
    
    # Find or create user
    existing_user = await db.users.find_one({"email": email}, {"_id": 0})
    
    if existing_user:
        user_id = existing_user["user_id"]
        await db.users.update_one(
            {"email": email},
            {"$set": {"name": name, "picture": picture}}
        )
    else:
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        user = User(
            user_id=user_id,
            email=email,
            name=name,
            picture=picture
        )
        await db.users.insert_one(user.model_dump())
    
    # Create session
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    session = UserSession(
        session_token=session_token,
        user_id=user_id,
        expires_at=expires_at
    )
    
    await db.user_sessions.delete_many({"user_id": user_id})
    await db.user_sessions.insert_one(session.model_dump())
    
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=7 * 24 * 60 * 60
    )
    
    user_doc = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    return user_doc

@api_router.get("/auth/me")
async def get_me(request: Request):
    """Get current authenticated user"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user.model_dump()

@api_router.post("/auth/logout")
async def logout(request: Request, response: Response):
    """Logout user"""
    session_token = request.cookies.get("session_token")
    if session_token:
        await db.user_sessions.delete_many({"session_token": session_token})
    
    response.delete_cookie(key="session_token", path="/")
    return {"message": "Logged out successfully"}

# ==================== PRODUCT ENDPOINTS (from Luxura API) ====================

@api_router.get("/products")
async def get_products(
    category: Optional[str] = None,
    search: Optional[str] = None,
    in_stock: Optional[bool] = None
):
    """Get all products from Luxura Inventory API"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{LUXURA_API_URL}/products")
            
            if response.status_code != 200:
                raise HTTPException(status_code=502, detail="Unable to fetch products from Luxura API")
            
            products = response.json()
            
            # Transform products for mobile app
            result = []
            for p in products:
                # Skip test products
                name = p.get('name', '')
                if 'test' in name.lower():
                    continue
                
                # Detect category
                product_category = detect_category(name)
                
                # Filter by category if specified
                if category and product_category != category:
                    continue
                
                # Filter by search if specified
                if search:
                    search_lower = search.lower()
                    if search_lower not in name.lower() and search_lower not in (p.get('sku') or '').lower():
                        continue
                
                # Filter by stock if specified
                is_in_stock = p.get('is_in_stock', False) or p.get('quantity', 0) > 0
                if in_stock is not None and is_in_stock != in_stock:
                    continue
                
                # Extract image from options
                options = p.get('options', {})
                image = extract_image_from_options(options)
                
                # Build Wix URL from handle
                handle = p.get('handle') or options.get('base', {}).get('handle')
                wix_url = f"https://www.luxuradistribution.com/product-page/{handle}" if handle else "https://www.luxuradistribution.com"
                
                result.append({
                    "id": p.get('id'),
                    "name": name,
                    "price": p.get('price', 0),
                    "description": p.get('description', ''),
                    "category": product_category,
                    "images": [image] if image else [get_category_image(product_category)],
                    "in_stock": is_in_stock,
                    "quantity": p.get('quantity', 0),
                    "sku": p.get('sku'),
                    "wix_url": wix_url,
                    "options": options
                })
            
            return result
            
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Luxura API timeout")
    except Exception as e:
        logger.error(f"Error fetching products: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/products/{product_id}")
async def get_product(product_id: int):
    """Get a single product from Luxura Inventory API"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{LUXURA_API_URL}/products/{product_id}")
            
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail="Product not found")
            
            if response.status_code != 200:
                raise HTTPException(status_code=502, detail="Unable to fetch product from Luxura API")
            
            p = response.json()
            
            # Transform for mobile app
            name = p.get('name', '')
            options = p.get('options', {})
            image = extract_image_from_options(options)
            handle = p.get('handle') or options.get('base', {}).get('handle')
            wix_url = f"https://www.luxuradistribution.com/product-page/{handle}" if handle else "https://www.luxuradistribution.com"
            
            return {
                "id": p.get('id'),
                "name": name,
                "price": p.get('price', 0),
                "description": p.get('description', ''),
                "category": detect_category(name),
                "images": [image] if image else ["https://static.wixstatic.com/media/de6cdb_df3cf3adbce44d49b39546b5178c459d~mv2.jpg"],
                "in_stock": p.get('is_in_stock', False) or p.get('quantity', 0) > 0,
                "quantity": p.get('quantity', 0),
                "sku": p.get('sku'),
                "wix_url": wix_url,
                "options": options
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching product: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== CATEGORY ENDPOINTS ====================

@api_router.get("/categories", response_model=List[Category])
async def get_categories():
    """Get all categories"""
    categories = [
        Category(id="genius", name="Genius", description="Extensions Genius Weft - Volume spectaculaire et confort", image="https://static.wixstatic.com/media/de6cdb_d16038b1f57044dabe702e8080aee3b4~mv2.jpg/v1/fill/w_600,h_600,q_85/pretty-woman-comic-book-art-full-body-shot.jpg", wix_url="https://www.luxuradistribution.com/genius", order=1),
        Category(id="halo", name="Halo", description="Extensions Halo - Effet naturel et invisible", image="https://static.wixstatic.com/media/de6cdb_6ad19e7a2a2749c8899daf8f972180fe~mv2.jpg/v1/fill/w_600,h_600,q_85/low-angle-young-woman-nature.jpg", wix_url="https://www.luxuradistribution.com/halo", order=2),
        Category(id="tape", name="Bande Adhésive", description="Extensions à bande adhésive professionnelle", image="https://static.wixstatic.com/media/de6cdb_8baf5d4bb6a14e0d9f8b302234b6f500~mv2.jpg/v1/fill/w_600,h_600,q_85/portrait-young-blonde-woman-with-with-tanned-skin-fashion-clothing.jpg", wix_url="https://www.luxuradistribution.com/tape", order=3),
        Category(id="i-tip", name="I-Tip", description="Extensions i-TIP - Précision et personnalisation", image="https://static.wixstatic.com/media/de6cdb_324e161652d54a5298af88e97359f00c~mv2.jpg/v1/fill/w_600,h_600,q_85/2024-11-29_11-29-28_edited.jpg", wix_url="https://www.luxuradistribution.com/i-tip", order=4),
        Category(id="essentiels", name="Essentiels", description="Outils et produits d'entretien professionnels", image="https://static.wixstatic.com/media/de6cdb_5ba6af2b449d44039ce9c23d3517953b~mv2.jpg/v1/fill/w_600,h_600,q_85/s-l1200.jpg", wix_url="https://www.luxuradistribution.com/essentiels", order=5),
    ]
    return categories

# ==================== CART ENDPOINTS ====================

@api_router.get("/cart")
async def get_cart(request: Request):
    """Get user's cart with product details"""
    user = await require_auth(request)
    
    cart_items = await db.cart_items.find(
        {"user_id": user.user_id},
        {"_id": 0}
    ).to_list(100)
    
    result = []
    total = 0
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for item in cart_items:
            try:
                response = await client.get(f"{LUXURA_API_URL}/products/{item['product_id']}")
                if response.status_code == 200:
                    p = response.json()
                    options = p.get('options', {})
                    image = extract_image_from_options(options)
                    
                    product_data = {
                        "id": p.get('id'),
                        "name": p.get('name', ''),
                        "price": p.get('price', 0),
                        "images": [image] if image else ["https://static.wixstatic.com/media/de6cdb_df3cf3adbce44d49b39546b5178c459d~mv2.jpg"],
                        "in_stock": p.get('is_in_stock', False)
                    }
                    
                    item_total = p.get('price', 0) * item['quantity']
                    total += item_total
                    
                    result.append({
                        "id": item["id"],
                        "product": product_data,
                        "quantity": item["quantity"],
                        "item_total": item_total
                    })
            except Exception as e:
                logger.error(f"Error fetching product for cart: {e}")
    
    return {"items": result, "total": total, "count": len(result)}

@api_router.post("/cart")
async def add_to_cart(item: CartItemCreate, request: Request):
    """Add item to cart"""
    user = await require_auth(request)
    
    # Verify product exists in Luxura API
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{LUXURA_API_URL}/products/{item.product_id}")
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="Product not found")
    
    # Check if item already in cart
    existing = await db.cart_items.find_one(
        {"user_id": user.user_id, "product_id": item.product_id},
        {"_id": 0}
    )
    
    if existing:
        new_quantity = existing["quantity"] + item.quantity
        await db.cart_items.update_one(
            {"id": existing["id"]},
            {"$set": {"quantity": new_quantity}}
        )
        return {"message": "Cart updated", "quantity": new_quantity}
    else:
        cart_item = CartItem(
            user_id=user.user_id,
            product_id=item.product_id,
            quantity=item.quantity
        )
        await db.cart_items.insert_one(cart_item.model_dump())
        return {"message": "Added to cart", "id": cart_item.id}

@api_router.put("/cart/{item_id}")
async def update_cart_item(item_id: str, update: CartItemUpdate, request: Request):
    """Update cart item quantity"""
    user = await require_auth(request)
    
    if update.quantity <= 0:
        await db.cart_items.delete_one({"id": item_id, "user_id": user.user_id})
        return {"message": "Item removed"}
    
    result = await db.cart_items.update_one(
        {"id": item_id, "user_id": user.user_id},
        {"$set": {"quantity": update.quantity}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Cart item not found")
    
    return {"message": "Cart updated"}

@api_router.delete("/cart/{item_id}")
async def remove_from_cart(item_id: str, request: Request):
    """Remove item from cart"""
    user = await require_auth(request)
    
    result = await db.cart_items.delete_one({"id": item_id, "user_id": user.user_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Cart item not found")
    
    return {"message": "Item removed"}

@api_router.delete("/cart")
async def clear_cart(request: Request):
    """Clear all items from cart"""
    user = await require_auth(request)
    await db.cart_items.delete_many({"user_id": user.user_id})
    return {"message": "Cart cleared"}

# ==================== BLOG ENDPOINTS ====================

@api_router.get("/blog")
async def get_blog_posts():
    """Get all blog posts"""
    posts = await db.blog_posts.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    if not posts:
        # Return default posts if none exist
        return [
            {
                "id": "entretien-extensions",
                "title": "Comment entretenir vos extensions capillaires",
                "content": "Les extensions capillaires nécessitent un entretien régulier pour maintenir leur beauté et leur durabilité.",
                "excerpt": "Découvrez nos conseils d'experts pour maintenir vos extensions capillaires en parfait état.",
                "image": "https://static.wixstatic.com/media/de6cdb_ed493ddeab524054935dfbf0714b7e29~mv2.jpg",
                "author": "Luxura Distribution",
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": "choisir-extensions",
                "title": "Guide: Choisir les bonnes extensions",
                "content": "Choisir les bonnes extensions capillaires peut sembler complexe. Voici notre guide complet.",
                "excerpt": "Tout ce que vous devez savoir pour choisir les extensions parfaites pour vous.",
                "image": "https://static.wixstatic.com/media/de6cdb_b293ba02614747dc8403c5de83ca1ae1~mv2.jpg",
                "author": "Luxura Distribution",
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": "tendances-2025",
                "title": "Tendances capillaires 2025",
                "content": "Les tendances capillaires de 2025 mettent l'accent sur le naturel et la personnalisation.",
                "excerpt": "Découvrez les tendances capillaires qui domineront 2025.",
                "image": "https://static.wixstatic.com/media/de6cdb_534f544ed92641e6811d56bd5dba5a67~mv2.jpg",
                "author": "Luxura Distribution",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        ]
    return posts

@api_router.get("/blog/{post_id}")
async def get_blog_post(post_id: str):
    """Get a single blog post"""
    post = await db.blog_posts.find_one({"id": post_id}, {"_id": 0})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post

# ==================== SALON ENDPOINTS ====================

@api_router.get("/salons")
async def get_salons(city: Optional[str] = None):
    """Get all partner salons from Luxura API or local DB"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{LUXURA_API_URL}/salons")
            if response.status_code == 200:
                salons = response.json()
                if city:
                    salons = [s for s in salons if city.lower() in s.get('city', '').lower()]
                return salons
    except Exception as e:
        logger.error(f"Error fetching salons from Luxura API: {e}")
    
    # Fallback to local DB
    query = {}
    if city:
        query["city"] = {"$regex": city, "$options": "i"}
    
    salons = await db.salons.find(query, {"_id": 0}).to_list(100)
    if not salons:
        return [
            {"id": "salon-1", "name": "Salon Carouso", "address": "123 Rue Principale", "city": "Montréal", "phone": "514-555-0001"},
            {"id": "salon-2", "name": "Salon Élégance", "address": "456 Boulevard Saint-Laurent", "city": "Montréal", "phone": "514-555-0002"},
            {"id": "salon-3", "name": "Coiffure Prestige", "address": "789 Avenue Cartier", "city": "Québec", "phone": "418-555-0003"},
        ]
    return salons

# ==================== HEALTH CHECK ====================

@api_router.get("/")
async def root():
    return {"message": "Luxura Distribution API", "status": "running", "inventory_api": LUXURA_API_URL}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
