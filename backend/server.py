from fastapi import FastAPI, APIRouter, HTTPException, Response, Request, Depends
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import httpx

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

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

class Product(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    price: float
    original_price: Optional[float] = None
    description: str
    category: str
    images: List[str] = []
    in_stock: bool = True
    color_code: Optional[str] = None
    series: Optional[str] = None
    wix_url: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ProductCreate(BaseModel):
    name: str
    price: float
    original_price: Optional[float] = None
    description: str
    category: str
    images: List[str] = []
    in_stock: bool = True
    color_code: Optional[str] = None
    series: Optional[str] = None
    wix_url: Optional[str] = None

class Category(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    image: Optional[str] = None
    wix_url: Optional[str] = None
    order: int = 0

class CartItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    product_id: str
    quantity: int = 1
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CartItemCreate(BaseModel):
    product_id: str
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
        # Update user data if needed
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
    
    # Delete old sessions for this user
    await db.user_sessions.delete_many({"user_id": user_id})
    await db.user_sessions.insert_one(session.model_dump())
    
    # Set cookie
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

# ==================== PRODUCT ENDPOINTS ====================

@api_router.get("/products", response_model=List[Product])
async def get_products(
    category: Optional[str] = None,
    search: Optional[str] = None,
    in_stock: Optional[bool] = None
):
    """Get all products with optional filtering"""
    query = {}
    
    if category:
        query["category"] = category
    if in_stock is not None:
        query["in_stock"] = in_stock
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
            {"color_code": {"$regex": search, "$options": "i"}}
        ]
    
    products = await db.products.find(query, {"_id": 0}).to_list(1000)
    return [Product(**p) for p in products]

@api_router.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: str):
    """Get a single product by ID"""
    product = await db.products.find_one({"id": product_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return Product(**product)

@api_router.post("/products", response_model=Product)
async def create_product(product: ProductCreate):
    """Create a new product (admin only in production)"""
    product_obj = Product(**product.model_dump())
    await db.products.insert_one(product_obj.model_dump())
    return product_obj

# ==================== CATEGORY ENDPOINTS ====================

@api_router.get("/categories", response_model=List[Category])
async def get_categories():
    """Get all categories"""
    categories = await db.categories.find({}, {"_id": 0}).sort("order", 1).to_list(100)
    return [Category(**c) for c in categories]

# ==================== CART ENDPOINTS ====================

@api_router.get("/cart")
async def get_cart(request: Request):
    """Get user's cart with product details"""
    user = await require_auth(request)
    
    cart_items = await db.cart_items.find(
        {"user_id": user.user_id},
        {"_id": 0}
    ).to_list(100)
    
    # Get product details for each item
    result = []
    total = 0
    for item in cart_items:
        product = await db.products.find_one({"id": item["product_id"]}, {"_id": 0})
        if product:
            item_total = product["price"] * item["quantity"]
            total += item_total
            result.append({
                "id": item["id"],
                "product": product,
                "quantity": item["quantity"],
                "item_total": item_total
            })
    
    return {"items": result, "total": total, "count": len(result)}

@api_router.post("/cart")
async def add_to_cart(item: CartItemCreate, request: Request):
    """Add item to cart"""
    user = await require_auth(request)
    
    # Check if product exists
    product = await db.products.find_one({"id": item.product_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Check if item already in cart
    existing = await db.cart_items.find_one(
        {"user_id": user.user_id, "product_id": item.product_id},
        {"_id": 0}
    )
    
    if existing:
        # Update quantity
        new_quantity = existing["quantity"] + item.quantity
        await db.cart_items.update_one(
            {"id": existing["id"]},
            {"$set": {"quantity": new_quantity}}
        )
        return {"message": "Cart updated", "quantity": new_quantity}
    else:
        # Add new item
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
        # Remove item if quantity is 0 or less
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

@api_router.get("/blog", response_model=List[BlogPost])
async def get_blog_posts():
    """Get all blog posts"""
    posts = await db.blog_posts.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return [BlogPost(**p) for p in posts]

@api_router.get("/blog/{post_id}", response_model=BlogPost)
async def get_blog_post(post_id: str):
    """Get a single blog post"""
    post = await db.blog_posts.find_one({"id": post_id}, {"_id": 0})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return BlogPost(**post)

# ==================== SALON ENDPOINTS ====================

@api_router.get("/salons", response_model=List[Salon])
async def get_salons(city: Optional[str] = None):
    """Get all partner salons"""
    query = {}
    if city:
        query["city"] = {"$regex": city, "$options": "i"}
    
    salons = await db.salons.find(query, {"_id": 0}).to_list(100)
    return [Salon(**s) for s in salons]

# ==================== SEED DATA ENDPOINT ====================

@api_router.post("/seed")
async def seed_data():
    """Seed initial data for the app"""
    
    # Clear existing data
    await db.categories.delete_many({})
    await db.products.delete_many({})
    await db.blog_posts.delete_many({})
    await db.salons.delete_many({})
    
    # Seed 5 categories from real Wix site
    categories = [
        Category(id="genius", name="Genius", description="Extensions Genius Weft - Volume spectaculaire et confort", image="https://static.wixstatic.com/media/de6cdb_d16038b1f57044dabe702e8080aee3b4~mv2.jpg/v1/fill/w_600,h_600,q_85/pretty-woman-comic-book-art-full-body-shot.jpg", wix_url="https://www.luxuradistribution.com/genius", order=1),
        Category(id="halo", name="Halo", description="Extensions Halo - Effet naturel et invisible", image="https://static.wixstatic.com/media/de6cdb_6ad19e7a2a2749c8899daf8f972180fe~mv2.jpg/v1/fill/w_600,h_600,q_85/low-angle-young-woman-nature.jpg", wix_url="https://www.luxuradistribution.com/halo", order=2),
        Category(id="tape", name="Bande Adhésive", description="Extensions à bande adhésive professionnelle", image="https://static.wixstatic.com/media/de6cdb_8baf5d4bb6a14e0d9f8b302234b6f500~mv2.jpg/v1/fill/w_600,h_600,q_85/portrait-young-blonde-woman-with-with-tanned-skin-fashion-clothing.jpg", wix_url="https://www.luxuradistribution.com/tape", order=3),
        Category(id="i-tip", name="I-Tip", description="Extensions i-TIP - Précision et personnalisation", image="https://static.wixstatic.com/media/de6cdb_324e161652d54a5298af88e97359f00c~mv2.jpg/v1/fill/w_600,h_600,q_85/2024-11-29_11-29-28_edited.jpg", wix_url="https://www.luxuradistribution.com/i-tip", order=4),
        Category(id="essentiels", name="Essentiels", description="Outils et produits d'entretien professionnels", image="https://static.wixstatic.com/media/de6cdb_5ba6af2b449d44039ce9c23d3517953b~mv2.jpg/v1/fill/w_600,h_600,q_85/s-l1200.jpg", wix_url="https://www.luxuradistribution.com/essentiels", order=5),
    ]
    
    for cat in categories:
        await db.categories.insert_one(cat.model_dump())
    
    # Seed products from real Wix data - GENIUS
    products = [
        # GENIUS WEFT
        Product(id="genius-noir-1", name="Genius Noir Foncé #1", price=249.95, description="Extensions Genius Weft série Vivian noir foncé. Trame invisible ultra-fine pour un résultat indétectable.", category="genius", images=["https://static.wixstatic.com/media/f1b961_0765bab9e407403289c86e98fcb27476~mv2.png"], color_code="#1", series="Vivian", wix_url="https://www.luxuradistribution.com/product-page/genius-trame-invisible-série-vivian-noir-foncé-1"),
        Product(id="genius-dc", name="Genius Dark Chocolate #DC", price=249.95, description="Extensions Genius Weft série Vivian chocolat foncé. Trame invisible pour une pose naturelle.", category="genius", images=["https://static.wixstatic.com/media/f1b961_58c11630ff1349728c47e56190218422~mv2.png"], color_code="#DC", series="Vivian", wix_url="https://www.luxuradistribution.com/product-page/genius-trame-invisible-série-vivian-dark-chocolate-dc"),
        Product(id="genius-ssd-cacao", name="Genius SSD Brun #CACAO", price=299.95, description="Extensions Genius Super Double Draw brun cacao. Volume maximum et densité exceptionnelle.", category="genius", images=["https://static.wixstatic.com/media/f1b961_11271a5d5d91485883888a201592829c~mv2.jpg"], color_code="#CACAO", series="Vivian SSD", wix_url="https://www.luxuradistribution.com/product-page/genius-ssd-trame-invisible-série-vivian-brun-cacao"),
        Product(id="genius-brun-2", name="Genius Brun #2", price=249.95, description="Extensions Genius Weft série Vivian brun naturel.", category="genius", images=["https://static.wixstatic.com/media/f1b961_2596437db6134f7bbdc1c5b2d72907fd~mv2.jpg"], color_code="#2", series="Vivian", wix_url="https://www.luxuradistribution.com/product-page/genius-trame-invisible-série-vivian-brun-2"),
        Product(id="genius-brun-moyen-3", name="Genius Brun Moyen #3", price=279.95, description="Extensions Genius Weft série Vivian brun moyen.", category="genius", images=["https://static.wixstatic.com/media/f1b961_47ff485b2f674fdc9245cc856004cd46~mv2.png"], color_code="#3", series="Vivian", wix_url="https://www.luxuradistribution.com/product-page/genius-trame-invisible-série-vivian-brun-moyen-3"),
        Product(id="genius-blond-6", name="Genius Brun Lumineux/Blond Foncé #6", price=269.95, description="Extensions Genius Weft série Vivian blond foncé lumineux.", category="genius", images=["https://static.wixstatic.com/media/f1b961_5769d9b826004a6f91eb9112dc140cfb~mv2.png"], color_code="#6", series="Vivian", wix_url="https://www.luxuradistribution.com/product-page/genius-série-vivian-brun-lumineux-blond-foncé-6"),
        Product(id="genius-foochow", name="Genius #Foochow", price=359.95, description="Extensions Genius Weft série Vivian collection Foochow. Couleur exclusive et raffinée.", category="genius", images=["https://static.wixstatic.com/media/f1b961_28d930f0f9924b229beb3be484bc1fbd~mv2.jpg"], color_code="#Foochow", series="Vivian", wix_url="https://www.luxuradistribution.com/product-page/genius-trame-invisible-série-vivian-foochow"),
        Product(id="genius-60a", name="Genius Blond Platine #60A", price=269.95, description="Extensions Genius Weft série Vivian blond platine.", category="genius", images=["https://static.wixstatic.com/media/f1b961_c3168b50e6d9464db8365cdef0b16557~mv2.png"], color_code="#60A", series="Vivian", wix_url="https://www.luxuradistribution.com/product-page/genius-trame-invisible-série-vivian-blond-platine-60a"),
        Product(id="genius-balayage-18-22", name="Genius Balayage Blond Beige #18/22", price=319.95, description="Extensions Genius Weft balayage blond beige.", category="genius", images=["https://static.wixstatic.com/media/f1b961_b7d3eb648bf443cb8d30e3e23fa62ad8~mv2.png"], color_code="#18/22", series="Vivian", wix_url="https://www.luxuradistribution.com/product-page/genius-trame-invisible-série-vivian-balayage-blond-beige-18-22"),
        Product(id="genius-balayage-6-24", name="Genius Balayage Blond Foncé #6/24", price=289.95, description="Extensions Genius Weft balayage blond foncé.", category="genius", images=["https://static.wixstatic.com/media/f1b961_387bbe6d47cd4217a7b0157f398d9a63~mv2.png"], color_code="#6/24", series="Vivian", wix_url="https://www.luxuradistribution.com/product-page/genius-trame-invisible-série-vivian-balayage-blond-foncé-6-24"),
        Product(id="genius-balayage-613-18a", name="Genius Balayage Blond Cendré #613/18A", price=319.95, description="Extensions Genius Weft balayage blond cendré.", category="genius", images=["https://static.wixstatic.com/media/f1b961_c15e5a01c6024a1699cb92a2be325f8f~mv2.png"], color_code="#613/18A", series="Vivian", wix_url="https://www.luxuradistribution.com/product-page/genius-série-vivian-balayage-blond-cendré-613-18a"),
        Product(id="genius-chengtu", name="Genius #ChengTu", price=359.95, description="Extensions Genius Weft série Vivian collection ChengTu.", category="genius", images=["https://static.wixstatic.com/media/f1b961_e440aecc44e44c69b0d56dad273a95e9~mv2.jpg"], color_code="#ChengTu", series="Vivian", wix_url="https://www.luxuradistribution.com/product-page/genius-trame-invisible-série-vivian-chengtu"),
        Product(id="genius-sdd-2btp18", name="Genius SDD Ombré #2BTP18/1006", price=354.95, description="Extensions Genius Super Double Draw ombré.", category="genius", images=["https://static.wixstatic.com/media/f1b961_75316de55cf441ecb82211cbc8d91010~mv2.jpg"], color_code="#2BTP18/1006", series="Vivian SDD", wix_url="https://www.luxuradistribution.com/product-page/genius-sdd-série-vivian-ombré-2btp18-1006"),
        Product(id="genius-ssd-5at60", name="Genius SSD Ombré Blond Cendré #5AT60", price=359.95, description="Extensions Genius Super Double Draw ombré blond cendré.", category="genius", images=["https://static.wixstatic.com/media/f1b961_9f8115b4f7614340b0dc9aeba39bd699~mv2.jpg"], color_code="#5AT60", series="Vivian SSD", wix_url="https://www.luxuradistribution.com/product-page/genius-ssd-série-vivian-ombré-blond-cendré-5at60"),
        Product(id="genius-ombre-cb", name="Genius Ombré Blond Miel #CB", price=319.95, description="Extensions Genius Weft ombré blond miel.", category="genius", images=["https://static.wixstatic.com/media/f1b961_5e027a0d94d749e99ad76830129b42da~mv2.png"], color_code="#CB", series="Vivian", wix_url="https://www.luxuradistribution.com/product-page/genius-série-vivian-ombré-blond-miel-cb"),
        
        # HALO
        Product(id="halo-1b", name="Halo série Everly Noir Doux/Brun Foncé #1B", price=239.95, description="Extensions Halo série Everly noir doux. Pose sans outil, pratiquement indétectable.", category="halo", images=["https://static.wixstatic.com/media/f1b961_42148bb43bbe484f9ca8f1127a4d30e4~mv2.png"], color_code="#1B", series="Everly", wix_url="https://www.luxuradistribution.com/product-page/halo-série-everly-noir-doux-brun-foncé-1b"),
        Product(id="halo-3", name="Halo série Everly Brun Moyen #3", price=239.95, description="Extensions Halo série Everly brun moyen.", category="halo", images=["https://static.wixstatic.com/media/f1b961_d1bb2905a7b748f5ac4676d5c96bae2a~mv2.png"], color_code="#3", series="Everly", wix_url="https://www.luxuradistribution.com/product-page/halo-série-everly-brun-moyen-3"),
        Product(id="halo-6", name="Halo série Everly Brun Lumineux/Blond Foncé #6", price=239.95, description="Extensions Halo série Everly blond foncé.", category="halo", images=["https://static.wixstatic.com/media/f1b961_5b61b7d6874a47abb7997a78d99c7125~mv2.png"], color_code="#6", series="Everly", wix_url="https://www.luxuradistribution.com/product-page/halo-série-everly-brun-lumineux-blond-foncé-6"),
        Product(id="halo-60a", name="Halo série Everly Blond Platine #60A", price=279.95, description="Extensions Halo série Everly blond platine.", category="halo", images=["https://static.wixstatic.com/media/f1b961_1e9953c3551440479117fa2954918173~mv2.png"], color_code="#60A", series="Everly", wix_url="https://www.luxuradistribution.com/product-page/halo-série-everly-blond-platine-60a"),
        Product(id="halo-balayage-6-24", name="Halo série Everly Balayage Blond Foncé #6/24", price=279.95, description="Extensions Halo série Everly balayage blond foncé.", category="halo", images=["https://static.wixstatic.com/media/f1b961_7858886b3ecb41e5bdf5be80b2aa4359~mv2.png"], color_code="#6/24", series="Everly", wix_url="https://www.luxuradistribution.com/product-page/halo-série-everly-balayage-blond-foncé-6-24"),
        Product(id="halo-balayage-613-18a", name="Halo série Everly Balayage Blond Cendré #613/18A", price=279.95, description="Extensions Halo série Everly balayage blond cendré.", category="halo", images=["https://static.wixstatic.com/media/f1b961_2fba27c18fe14584a828cfa9880a3146~mv2.png"], color_code="#613/18A", series="Everly", wix_url="https://www.luxuradistribution.com/product-page/halo-série-everly-balayage-blond-cendré-613-18a"),
        Product(id="halo-balayage-18-22", name="Halo série Everly Balayage Blond Beige #18/22", price=279.95, description="Extensions Halo série Everly balayage blond beige.", category="halo", images=["https://static.wixstatic.com/media/f1b961_ed52f5195856485796099c2a1823a0fd~mv2.png"], color_code="#18/22", series="Everly", wix_url="https://www.luxuradistribution.com/product-page/halo-série-everly-balayage-blond-beige-18-22"),
        Product(id="halo-ombre-cb", name="Halo série Everly Ombré Blond Miel #CB", price=299.95, description="Extensions Halo série Everly ombré blond miel.", category="halo", images=["https://static.wixstatic.com/media/f1b961_7ba6134ca87e4423817e9b0fa07754c1~mv2.png"], color_code="#CB", series="Everly", wix_url="https://www.luxuradistribution.com/product-page/halo-série-everly-ombré-blond-miel-cb"),
        
        # BANDE ADHESIVE (TAPE)
        Product(id="tape-icw", name="Bande Invisible Ice White #ICW", price=289.95, description="Extensions à bande adhésive professionnelle Ice White. Série Salon Professionnelle Aurora.", category="tape", images=["https://static.wixstatic.com/media/f1b961_9b2d02f5f8fe47369534f67678bbc79d~mv2.jpg"], color_code="#ICW", series="Aurora", wix_url="https://www.luxuradistribution.com/product-page/bande-invisible-série-aurora-ice-white-icw"),
        Product(id="tape-dc", name="Bande Adhésive Dark Chocolate #DC", price=84.95, description="Extensions à bande adhésive série Aurora chocolat foncé.", category="tape", images=["https://static.wixstatic.com/media/f1b961_fa7cd15003c94b16a263bd39d22dc48c~mv2.jpg"], color_code="#DC", series="Aurora", wix_url="https://www.luxuradistribution.com/product-page/bande-adhésive-série-aurora-dark-chocolate-dc"),
        Product(id="tape-pha", name="Bande Adhésive Blond #PHA", price=99.95, description="Extensions à bande adhésive série Aurora blond.", category="tape", images=["https://static.wixstatic.com/media/f1b961_9b2d02f5f8fe47369534f67678bbc79d~mv2.jpg"], color_code="#PHA", series="Aurora", wix_url="https://www.luxuradistribution.com/product-page/bande-adhésive-série-aurora-blond-pha"),
        Product(id="tape-1", name="Bande Adhésive Noir Foncé #1", price=84.95, description="Extensions à bande adhésive série Aurora noir foncé.", category="tape", images=["https://static.wixstatic.com/media/f1b961_8bed6fa0069a41c3971d7dcb51ab1cec~mv2.png"], color_code="#1", series="Aurora", wix_url="https://www.luxuradistribution.com/product-page/bande-adhésive-série-aurora-noir-foncé-1-jet-black"),
        Product(id="tape-1b", name="Bande Adhésive Brun Foncé #1B", price=84.95, description="Extensions à bande adhésive série Aurora brun foncé.", category="tape", images=["https://static.wixstatic.com/media/f1b961_088e24bf74854319bab62d49634b608a~mv2.png"], color_code="#1B", series="Aurora", wix_url="https://www.luxuradistribution.com/product-page/bande-adhésive-série-aurora-brun-foncé-noir-doux-1b"),
        Product(id="tape-6", name="Bande Adhésive Blond Foncé #6", price=84.95, description="Extensions à bande adhésive série Aurora blond foncé.", category="tape", images=["https://static.wixstatic.com/media/f1b961_5d6668fdf8114e3d99f528fe612222f0~mv2.png"], color_code="#6", series="Aurora", wix_url="https://www.luxuradistribution.com/product-page/bande-adhésive-série-aurora-brun-lumineux-blond-foncé-6"),
        Product(id="tape-3", name="Bande Adhésive Brun Moyen #3", price=84.95, description="Extensions à bande adhésive série Aurora brun moyen.", category="tape", images=["https://static.wixstatic.com/media/f1b961_a0bb462af6f44e25aa751ea359024bba~mv2.png"], color_code="#3", series="Aurora", wix_url="https://www.luxuradistribution.com/product-page/bande-adhésive-série-aurora-brun-moyen-3"),
        
        # I-TIP
        Product(id="itip-1b", name="I-Tips série Eleanor Brun Foncé #1B", price=89.95, description="Extensions i-TIP série Eleanor brun foncé. Application mèche par mèche précise.", category="i-tip", images=["https://static.wixstatic.com/media/f1b961_0d440382da1f450da579fd73c14daf88~mv2.png"], color_code="#1B", series="Eleanor", wix_url="https://www.luxuradistribution.com/product-page/i-tips-série-eleanor-brun-foncé-noir-doux-1b"),
        Product(id="itip-3", name="I-Tips série Eleanor Brun Moyen #3", price=89.95, description="Extensions i-TIP série Eleanor brun moyen.", category="i-tip", images=["https://static.wixstatic.com/media/f1b961_700df468de3d47fd858254135ef25077~mv2.png"], color_code="#3", series="Eleanor", wix_url="https://www.luxuradistribution.com/product-page/i-tips-série-eleanor-brun-moyen-3"),
        Product(id="itip-6", name="I-Tips série Eleanor Blond Foncé #6", price=89.95, description="Extensions i-TIP série Eleanor blond foncé.", category="i-tip", images=["https://static.wixstatic.com/media/f1b961_a57ce713f15e44b1b34b23d3fb93aae2~mv2.png"], color_code="#6", series="Eleanor", wix_url="https://www.luxuradistribution.com/product-page/i-tips-série-eleanor-brun-lumineux-blond-foncé-6"),
        Product(id="itip-60a", name="I-Tips série Eleanor Blond Platine #60A", price=104.95, description="Extensions i-TIP série Eleanor blond platine.", category="i-tip", images=["https://static.wixstatic.com/media/f1b961_f9c55a90f028493cb6339c71ef4e57fb~mv2.png"], color_code="#60A", series="Eleanor", wix_url="https://www.luxuradistribution.com/product-page/i-tips-série-eleanor-blond-platine-60a"),
        Product(id="itip-balayage-613-18a", name="I-Tips série Eleanor Balayage Blond Cendré #613/18A", price=104.95, description="Extensions i-TIP série Eleanor balayage blond cendré.", category="i-tip", images=["https://static.wixstatic.com/media/f1b961_b8fed8c42a434fa89db241a66d0db9a1~mv2.png"], color_code="#613/18A", series="Eleanor", wix_url="https://www.luxuradistribution.com/product-page/i-tips-série-eleanor-balayage-blond-cendré-613-18a"),
        Product(id="itip-ombre-cb", name="I-Tips série Eleanor Ombré Blond Miel #CB", price=119.95, description="Extensions i-TIP série Eleanor ombré blond miel.", category="i-tip", images=["https://static.wixstatic.com/media/f1b961_bcfc6629dd584b24bd14773026d487e6~mv2.png"], color_code="#CB", series="Eleanor", wix_url="https://www.luxuradistribution.com/product-page/i-tips-série-eleanor-ombré-blond-miel-cb"),
        
        # ESSENTIELS
        Product(id="brosse-volumisante", name="Brosse Volumisante et Séchante", price=89.95, original_price=129.95, description="Brosse volumisante et séchante professionnelle pour extensions.", category="essentiels", images=["https://static.wixstatic.com/media/de6cdb_1977c4f9e78645a38131eaa992c478ce~mv2.jpg"], wix_url="https://www.luxuradistribution.com/product-page/brosse-volumisante-et-séchante"),
        Product(id="fer-friser", name="Fer à Friser Rotatif", price=99.95, description="Fer à friser rotatif professionnel.", category="essentiels", images=["https://static.wixstatic.com/media/f1b961_c2a4294fb20e4f85886c08aaa766ee96~mv2.jpg"], wix_url="https://www.luxuradistribution.com/product-page/fer-à-friser-rotatif"),
        Product(id="ensemble-installation", name="Ensemble Installation", price=249.95, description="Ensemble complet d'installation pour extensions. Gratuit avec formation.", category="essentiels", images=["https://static.wixstatic.com/media/f1b961_c0dc66d5b2374e2282c96d236dee6175~mv2.jpg"], wix_url="https://www.luxuradistribution.com/product-page/ensemble-installation"),
        Product(id="coffret-huile", name="Coffret Huile d'Étoile", price=69.95, description="Coffret huile d'étoile pour entretien des extensions.", category="essentiels", images=["https://static.wixstatic.com/media/f1b961_b48ec5e3f7f24fc3bdd9e2613979fc71~mv2.jpg"], wix_url="https://www.luxuradistribution.com/product-page/coffret-huile-d-étoile"),
        Product(id="bande-adhesive-tenue", name="Bande Adhésive Tenue Ultra", price=17.95, description="Bande adhésive de remplacement tenue ultra.", category="essentiels", images=["https://static.wixstatic.com/media/f1b961_4791f6eeb5d24fcfae259a9ef0880587~mv2.png"], wix_url="https://www.luxuradistribution.com/product-page/bande-adhésive-tenue-ultra"),
        Product(id="anneau-couleur", name="Anneau de Couleur Haut de Gamme", price=299.95, description="Anneau de couleur professionnel haut de gamme.", category="essentiels", images=["https://static.wixstatic.com/media/f1b961_7e0034e9662d46b1a20dbbd6ee6ae1df~mv2.jpg"], wix_url="https://www.luxuradistribution.com/product-page/anneau-de-couleur-haut-de-gamme"),
        Product(id="spray-just-rite", name="Spray de Positionnement JUST-RITE", price=29.95, description="Spray de positionnement pour application des extensions.", category="essentiels", images=["https://static.wixstatic.com/media/f1b961_66cf8bb6c72d4883b33c79999dc0e8cd~mv2.jpg"], wix_url="https://www.luxuradistribution.com/product-page/spray-de-positionnement-just-rite"),
        Product(id="pince-application", name="Pince d'Application Bande Adhésive", price=59.95, description="Pince professionnelle pour application de bande adhésive.", category="essentiels", images=["https://static.wixstatic.com/media/f1b961_f0f73594164646a5b80c9dc139d487b9~mv2.jpg"], wix_url="https://www.luxuradistribution.com/product-page/pince-d-application-bande-adhésive"),
    ]
    
    for prod in products:
        await db.products.insert_one(prod.model_dump())
    
    # Seed blog posts
    blog_posts = [
        BlogPost(
            id="entretien-extensions",
            title="Comment entretenir vos extensions capillaires",
            content="Les extensions capillaires nécessitent un entretien régulier pour maintenir leur beauté et leur durabilité. Voici nos conseils d'experts:\n\n1. **Brossage quotidien**: Utilisez une brosse spéciale extensions pour démêler délicatement vos cheveux, en commençant par les pointes.\n\n2. **Lavage**: Lavez vos extensions 2-3 fois par semaine maximum avec un shampooing sans sulfate. Évitez de frotter vigoureusement.\n\n3. **Séchage**: Laissez sécher naturellement autant que possible. Si vous utilisez un sèche-cheveux, réglez-le sur température basse.\n\n4. **Produits**: Utilisez des produits spécialement formulés pour les extensions, comme la gamme Medavita que nous proposons.\n\n5. **Nuit**: Tressez légèrement vos cheveux avant de dormir pour éviter les nœuds.",
            excerpt="Découvrez nos conseils d'experts pour maintenir vos extensions capillaires en parfait état.",
            image="https://static.wixstatic.com/media/de6cdb_ed493ddeab524054935dfbf0714b7e29~mv2.jpg"
        ),
        BlogPost(
            id="choisir-extensions",
            title="Guide: Choisir les bonnes extensions",
            content="Choisir les bonnes extensions capillaires peut sembler complexe. Voici notre guide complet:\n\n**Type d'extensions:**\n- **Genius Weft**: Idéal pour un look naturel et une pose rapide. La trame ultra-fine est indétectable.\n- **Halo**: Parfait pour un essai sans engagement. Pose sans outil en quelques secondes.\n- **Bande Adhésive**: Pour ajouter du volume avec flexibilité.\n- **I-Tip**: Application mèche par mèche pour une personnalisation maximale.\n\n**Couleur:**\nChoisissez une couleur qui correspond à vos cheveux naturels ou optez pour un balayage/ombré pour un effet tendance.\n\n**Qualité:**\nToutes nos extensions sont en cheveux 100% naturels Remy Hair, garantissant une qualité supérieure et une durabilité exceptionnelle.",
            excerpt="Tout ce que vous devez savoir pour choisir les extensions parfaites pour vous.",
            image="https://static.wixstatic.com/media/de6cdb_b293ba02614747dc8403c5de83ca1ae1~mv2.jpg"
        ),
        BlogPost(
            id="tendances-2025",
            title="Tendances capillaires 2025",
            content="Les tendances capillaires de 2025 mettent l'accent sur le naturel et la personnalisation:\n\n**1. Balayage naturel**\nLes transitions douces entre les couleurs restent très populaires. Nos extensions balayage sont parfaites pour ce look.\n\n**2. Longueurs XXL**\nLes cheveux longs font leur grand retour. Nos extensions permettent d'atteindre la longueur désirée instantanément.\n\n**3. Textures naturelles**\nEmbrasser sa texture naturelle est tendance. Nos extensions Remy Hair s'adaptent à tous les types de cheveux.\n\n**4. Blonds nordiques**\nLes blonds froids et cendrés sont très demandés cette année. Découvrez nos teintes #613/18A et Ice White.\n\n**5. Bruns riches**\nLes bruns chocolat et moka apportent profondeur et sophistication.",
            excerpt="Découvrez les tendances capillaires qui domineront 2025.",
            image="https://static.wixstatic.com/media/de6cdb_534f544ed92641e6811d56bd5dba5a67~mv2.jpg"
        )
    ]
    
    for post in blog_posts:
        await db.blog_posts.insert_one(post.model_dump())
    
    # Seed salons
    salons = [
        Salon(id="salon-carouso", name="Salon Carouso", address="123 Rue Principale", city="Montréal", phone="514-555-0001", website="https://www.saloncarouso.com/"),
        Salon(id="salon-elegance", name="Salon Élégance", address="456 Boulevard Saint-Laurent", city="Montréal", phone="514-555-0002"),
        Salon(id="coiffure-prestige", name="Coiffure Prestige", address="789 Avenue Cartier", city="Québec", phone="418-555-0003"),
        Salon(id="studio-beaute", name="Studio Beauté", address="321 Rue King", city="Sherbrooke", phone="819-555-0004"),
        Salon(id="hair-studio-laval", name="Hair Studio Laval", address="654 Boulevard Curé-Labelle", city="Laval", phone="450-555-0005"),
        Salon(id="salon-chic", name="Salon Chic", address="987 Rue Notre-Dame", city="Trois-Rivières", phone="819-555-0006"),
    ]
    
    for salon in salons:
        await db.salons.insert_one(salon.model_dump())
    
    return {
        "message": "Data seeded successfully",
        "categories": len(categories),
        "products": len(products),
        "blog_posts": len(blog_posts),
        "salons": len(salons)
    }

# ==================== HEALTH CHECK ====================

@api_router.get("/")
async def root():
    return {"message": "Luxura Distribution API", "status": "running"}

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
