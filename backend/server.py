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
    description: str
    category: str
    images: List[str] = []
    in_stock: bool = True
    color_code: Optional[str] = None
    series: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ProductCreate(BaseModel):
    name: str
    price: float
    description: str
    category: str
    images: List[str] = []
    in_stock: bool = True
    color_code: Optional[str] = None
    series: Optional[str] = None

class Category(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    image: Optional[str] = None
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
    
    # Seed categories
    categories = [
        Category(id="genius-weft", name="Genius Weft", description="Extensions à trame invisible ultra-fine", image="https://static.wixstatic.com/media/f1b961_0765bab9e407403289c86e98fcb27476~mv2.png", order=1),
        Category(id="bande-invisible", name="Bande Invisible", description="Extensions adhésives professionnelles", image="https://static.wixstatic.com/media/f1b961_9b2d02f5f8fe47369534f67678bbc79d~mv2.jpg", order=2),
        Category(id="genius-ssd", name="Genius SSD", description="Super Double Draw - Volume maximum", image="https://static.wixstatic.com/media/f1b961_11271a5d5d91485883888a201592829c~mv2.jpg", order=3),
        Category(id="essentiels", name="Essentiels", description="Outils et produits d'entretien", image="https://static.wixstatic.com/media/de6cdb_376a86d30d59471d80f4511a6704664d~mv2.jpg", order=4),
    ]
    
    for cat in categories:
        await db.categories.insert_one(cat.model_dump())
    
    # Seed products
    products = [
        Product(id="genius-noir-1", name="Genius Noir Foncé #1", price=249.95, description="Extensions Genius Weft en noir foncé naturel. Trame invisible ultra-fine pour un résultat indétectable. Cheveux 100% naturels Remy Hair.", category="genius-weft", images=["https://static.wixstatic.com/media/f1b961_0765bab9e407403289c86e98fcb27476~mv2.png"], color_code="#1", series="Vivian"),
        Product(id="genius-dc", name="Genius Dark Chocolate #DC", price=249.95, description="Extensions Genius Weft chocolat foncé. Trame invisible pour une pose naturelle et confortable.", category="genius-weft", images=["https://static.wixstatic.com/media/f1b961_58c11630ff1349728c47e56190218422~mv2.png"], color_code="#DC", series="Vivian"),
        Product(id="genius-brun-2", name="Genius Brun #2", price=249.95, description="Extensions Genius Weft brun naturel. Qualité professionnelle Remy Hair.", category="genius-weft", images=["https://static.wixstatic.com/media/f1b961_2596437db6134f7bbdc1c5b2d72907fd~mv2.jpg"], color_code="#2", series="Vivian"),
        Product(id="genius-brun-moyen-3", name="Genius Brun Moyen #3", price=279.95, description="Extensions Genius Weft brun moyen. Texture soyeuse et naturelle.", category="genius-weft", images=["https://static.wixstatic.com/media/f1b961_47ff485b2f674fdc9245cc856004cd46~mv2.png"], color_code="#3", series="Vivian"),
        Product(id="genius-blond-6", name="Genius Blond Foncé #6", price=269.95, description="Extensions Genius Weft blond foncé lumineux. Cheveux naturels de qualité supérieure.", category="genius-weft", images=["https://static.wixstatic.com/media/f1b961_5769d9b826004a6f91eb9112dc140cfb~mv2.png"], color_code="#6", series="Vivian"),
        Product(id="genius-balayage-6-24", name="Genius Balayage Blond Foncé #6/24", price=289.95, description="Extensions Genius Weft effet balayage naturel. Mélange de tons pour un look tendance.", category="genius-weft", images=["https://static.wixstatic.com/media/f1b961_387bbe6d47cd4217a7b0157f398d9a63~mv2.png"], color_code="#6/24", series="Vivian"),
        Product(id="genius-balayage-18-22", name="Genius Balayage Blond Beige #18/22", price=319.95, description="Extensions Genius Weft balayage blond beige. Aspect naturel et lumineux.", category="genius-weft", images=["https://static.wixstatic.com/media/f1b961_b7d3eb648bf443cb8d30e3e23fa62ad8~mv2.png"], color_code="#18/22", series="Vivian"),
        Product(id="genius-ombre-3-3t24", name="Genius Ombré Brun Cacao #3/3T24", price=319.95, description="Extensions Genius Weft effet ombré du brun au blond. Transition naturelle.", category="genius-weft", images=["https://static.wixstatic.com/media/f1b961_f7c08b4eeb9d454aa0da2db110ab359d~mv2.png"], color_code="#3/3T24", series="Vivian"),
        Product(id="genius-ombre-db", name="Genius Ombré Brun Nuit #DB", price=319.95, description="Extensions Genius Weft ombré brun nuit. Profondeur et dimension.", category="genius-weft", images=["https://static.wixstatic.com/media/f1b961_b049d0356ab04230a0291ddadc1dfbe8~mv2.png"], color_code="#DB", series="Vivian"),
        Product(id="genius-balayage-613-18a", name="Genius Balayage Blond Cendré #613/18A", price=319.95, description="Extensions Genius Weft balayage blond cendré. Look nordique élégant.", category="genius-weft", images=["https://static.wixstatic.com/media/f1b961_c15e5a01c6024a1699cb92a2be325f8f~mv2.png"], color_code="#613/18A", series="Vivian"),
        Product(id="genius-ombre-hps", name="Genius Ombré Blond Cendré #HPS", price=349.95, description="Extensions Genius Weft ombré blond cendré premium. Finition luxueuse.", category="genius-weft", images=["https://static.wixstatic.com/media/f1b961_46c106d70c154c34918e15ad23452fc4~mv2.png"], color_code="#HPS", series="Vivian"),
        Product(id="genius-ombre-6-6t24", name="Genius Ombré Blond Moka #6/6T24", price=349.95, description="Extensions Genius Weft ombré blond moka. Chaleur et luminosité.", category="genius-weft", images=["https://static.wixstatic.com/media/f1b961_b1da0ecc4ce04c86955047f5f172a44c~mv2.png"], color_code="#6/6T24", series="Vivian"),
        Product(id="genius-foochow", name="Genius Foochow", price=359.95, description="Extensions Genius Weft collection Foochow. Couleur exclusive et raffinée.", category="genius-weft", images=["https://static.wixstatic.com/media/f1b961_28d930f0f9924b229beb3be484bc1fbd~mv2.jpg"], color_code="Foochow", series="Vivian"),
        Product(id="genius-chengtu", name="Genius ChengTu", price=359.95, description="Extensions Genius Weft collection ChengTu. Élégance asiatique.", category="genius-weft", images=["https://static.wixstatic.com/media/f1b961_e440aecc44e44c69b0d56dad273a95e9~mv2.jpg"], color_code="ChengTu", series="Vivian"),
        Product(id="genius-5atp18b62", name="Genius #5ATP18B62", price=349.95, description="Extensions Genius Weft mélange de tons blonds. Look multidimensionnel.", category="genius-weft", images=["https://static.wixstatic.com/media/f1b961_0e7cf48e1d59418bbf1b562c21494176~mv2.jpg"], color_code="#5ATP18B62", series="Vivian"),
        
        # Bande Invisible
        Product(id="bande-icw", name="Bande Invisible Ice White #ICW", price=289.95, description="Extensions à bande adhésive professionnelle blanc glacé. Série Salon Professionnelle Aurora.", category="bande-invisible", images=["https://static.wixstatic.com/media/f1b961_9b2d02f5f8fe47369534f67678bbc79d~mv2.jpg"], color_code="#ICW", series="Aurora"),
        
        # Genius SSD
        Product(id="genius-ssd-cacao", name="Genius SSD Brun #CACAO", price=299.95, description="Extensions Genius Super Double Draw brun cacao. Volume maximum et densité exceptionnelle.", category="genius-ssd", images=["https://static.wixstatic.com/media/f1b961_11271a5d5d91485883888a201592829c~mv2.jpg"], color_code="#CACAO", series="Vivian SSD"),
        Product(id="genius-sdd-2btp18", name="Genius SDD Ombré #2BTP18/1006", price=354.95, description="Extensions Genius Super Double Draw ombré. Transition de couleurs parfaite.", category="genius-ssd", images=["https://static.wixstatic.com/media/f1b961_75316de55cf441ecb82211cbc8d91010~mv2.jpg"], color_code="#2BTP18/1006", series="Vivian SDD"),
        Product(id="genius-ssd-5at60", name="Genius SSD Ombré Blond Cendré #5AT60", price=359.95, description="Extensions Genius Super Double Draw ombré blond cendré. Finition premium.", category="genius-ssd", images=["https://static.wixstatic.com/media/f1b961_9f8115b4f7614340b0dc9aeba39bd699~mv2.jpg"], color_code="#5AT60", series="Vivian SSD"),
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
            content="Choisir les bonnes extensions capillaires peut sembler complexe. Voici notre guide complet:\n\n**Type d'extensions:**\n- **Genius Weft**: Idéal pour un look naturel et une pose rapide. La trame ultra-fine est indétectable.\n- **Bandes adhésives**: Parfait pour ajouter du volume sans engagement permanent.\n- **Super Double Draw (SSD)**: Pour un volume maximum de la racine aux pointes.\n\n**Couleur:**\nChoisissez une couleur qui correspond à vos cheveux naturels ou optez pour un balayage/ombré pour un effet tendance.\n\n**Longueur:**\nNos extensions sont disponibles en différentes longueurs. Consultez un professionnel pour déterminer celle qui convient à votre style de vie.\n\n**Qualité:**\nToutes nos extensions sont en cheveux 100% naturels Remy Hair, garantissant une qualité supérieure et une durabilité exceptionnelle.",
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
