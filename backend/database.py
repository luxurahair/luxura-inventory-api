"""
LUXURA DATABASE - Supabase/PostgreSQL Layer
============================================
Remplace toutes les opérations MongoDB par SQLAlchemy/PostgreSQL.
"""

import os
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import create_engine, Column, String, Integer, Text, Boolean, DateTime, ForeignKey, desc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func

logger = logging.getLogger(__name__)

# ============================================
# DATABASE CONNECTION
# ============================================

DATABASE_URL = os.environ.get('DATABASE_URL', '')
engine = None
SessionLocal = None
Base = declarative_base()

if DATABASE_URL:
    # Fix pour Render/Supabase: remplacer postgres:// par postgresql://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    try:
        # Configuration améliorée pour éviter les timeouts Supabase
        engine = create_engine(
            DATABASE_URL, 
            pool_pre_ping=True,      # Vérifie la connexion avant utilisation
            pool_recycle=300,        # Recycle les connexions après 5 min
            pool_size=5,             # Nombre de connexions dans le pool
            max_overflow=10,         # Connexions supplémentaires si besoin
            pool_timeout=30,         # Timeout pour obtenir une connexion du pool
            connect_args={
                "connect_timeout": 10,    # Timeout connexion initiale (10s)
                "options": "-c statement_timeout=30000"  # Timeout requête (30s)
            }
        )
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        logger.info("✅ Database engine created with improved timeout settings")
    except Exception as e:
        logger.error(f"❌ Database connection error: {e}")
        engine = None
        SessionLocal = None

# ============================================
# MODELS SQLAlchemy
# ============================================

class UserDB(Base):
    __tablename__ = "users"
    user_id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    picture = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class UserSessionDB(Base):
    __tablename__ = "user_sessions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_token = Column(String, unique=True, nullable=False)
    user_id = Column(String, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class CartItemDB(Base):
    __tablename__ = "cart_items"
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    product_id = Column(Integer, nullable=False)
    quantity = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class BlogPostDB(Base):
    __tablename__ = "blog_posts"
    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    excerpt = Column(Text, nullable=True)
    image = Column(String, nullable=True)
    author = Column(String, default="Luxura Distribution")
    wix_post_id = Column(String, nullable=True)
    published_to_wix = Column(Boolean, default=False)
    published_to_facebook = Column(Boolean, default=False)
    pushed_to_wix = Column(Boolean, default=False)
    auto_generated = Column(Boolean, default=False)
    category = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class SEOLogDB(Base):
    __tablename__ = "seo_generation_log"
    id = Column(Integer, primary_key=True, autoincrement=True)
    blog_id = Column(String, nullable=True)
    title = Column(String, nullable=True)
    category = Column(String, nullable=True)
    date = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String, default="generated")

class BacklinkRunDB(Base):
    __tablename__ = "backlink_runs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    directory = Column(String, nullable=True)
    status = Column(String, nullable=True)
    message = Column(String, nullable=True)
    date = Column(DateTime(timezone=True), server_default=func.now())

class SalonDB(Base):
    __tablename__ = "salons"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    address = Column(String, nullable=True)
    city = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    website = Column(String, nullable=True)
    latitude = Column(String, nullable=True)
    longitude = Column(String, nullable=True)

# ============================================
# INIT DATABASE
# ============================================

def init_db():
    """Créer les tables si elles n'existent pas"""
    if engine:
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("✅ Database tables created/verified")
            return True
        except Exception as e:
            logger.error(f"❌ Error creating tables: {e}")
            return False
    return False

def get_db_session() -> Optional[Session]:
    """Obtenir une session de base de données"""
    if SessionLocal is None:
        return None
    return SessionLocal()

# ============================================
# USER FUNCTIONS
# ============================================

async def db_get_user_by_email(email: str) -> Optional[Dict]:
    """Trouver un utilisateur par email"""
    session = get_db_session()
    if not session:
        return None
    try:
        user = session.query(UserDB).filter(UserDB.email == email).first()
        if user:
            return {
                "user_id": user.user_id,
                "email": user.email,
                "name": user.name,
                "picture": user.picture,
                "created_at": user.created_at
            }
        return None
    finally:
        session.close()

async def db_get_user_by_id(user_id: str) -> Optional[Dict]:
    """Trouver un utilisateur par ID"""
    session = get_db_session()
    if not session:
        return None
    try:
        user = session.query(UserDB).filter(UserDB.user_id == user_id).first()
        if user:
            return {
                "user_id": user.user_id,
                "email": user.email,
                "name": user.name,
                "picture": user.picture,
                "created_at": user.created_at
            }
        return None
    finally:
        session.close()

async def db_create_user(user_id: str, email: str, name: str, picture: str = None) -> bool:
    """Créer un nouvel utilisateur"""
    session = get_db_session()
    if not session:
        return False
    try:
        user = UserDB(user_id=user_id, email=email, name=name, picture=picture)
        session.add(user)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating user: {e}")
        return False
    finally:
        session.close()

async def db_update_user(email: str, name: str, picture: str = None) -> bool:
    """Mettre à jour un utilisateur"""
    session = get_db_session()
    if not session:
        return False
    try:
        user = session.query(UserDB).filter(UserDB.email == email).first()
        if user:
            user.name = name
            user.picture = picture
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        logger.error(f"Error updating user: {e}")
        return False
    finally:
        session.close()

# ============================================
# SESSION FUNCTIONS
# ============================================

async def db_get_session(session_token: str) -> Optional[Dict]:
    """Trouver une session par token"""
    session = get_db_session()
    if not session:
        return None
    try:
        sess = session.query(UserSessionDB).filter(UserSessionDB.session_token == session_token).first()
        if sess:
            return {
                "session_token": sess.session_token,
                "user_id": sess.user_id,
                "expires_at": sess.expires_at,
                "created_at": sess.created_at
            }
        return None
    finally:
        session.close()

async def db_create_session(session_token: str, user_id: str, expires_at: datetime) -> bool:
    """Créer une nouvelle session"""
    session = get_db_session()
    if not session:
        return False
    try:
        sess = UserSessionDB(session_token=session_token, user_id=user_id, expires_at=expires_at)
        session.add(sess)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating session: {e}")
        return False
    finally:
        session.close()

async def db_delete_user_sessions(user_id: str) -> bool:
    """Supprimer toutes les sessions d'un utilisateur"""
    session = get_db_session()
    if not session:
        return False
    try:
        session.query(UserSessionDB).filter(UserSessionDB.user_id == user_id).delete()
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        logger.error(f"Error deleting sessions: {e}")
        return False
    finally:
        session.close()

async def db_delete_session(session_token: str) -> bool:
    """Supprimer une session spécifique"""
    session = get_db_session()
    if not session:
        return False
    try:
        session.query(UserSessionDB).filter(UserSessionDB.session_token == session_token).delete()
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        logger.error(f"Error deleting session: {e}")
        return False
    finally:
        session.close()

# ============================================
# CART FUNCTIONS
# ============================================

async def db_get_cart_items(user_id: str) -> List[Dict]:
    """Obtenir tous les items du panier d'un utilisateur"""
    session = get_db_session()
    if not session:
        return []
    try:
        items = session.query(CartItemDB).filter(CartItemDB.user_id == user_id).all()
        return [
            {
                "id": item.id,
                "user_id": item.user_id,
                "product_id": item.product_id,
                "quantity": item.quantity,
                "created_at": item.created_at
            }
            for item in items
        ]
    finally:
        session.close()

async def db_get_cart_item(user_id: str, product_id: int) -> Optional[Dict]:
    """Trouver un item spécifique dans le panier"""
    session = get_db_session()
    if not session:
        return None
    try:
        item = session.query(CartItemDB).filter(
            CartItemDB.user_id == user_id,
            CartItemDB.product_id == product_id
        ).first()
        if item:
            return {
                "id": item.id,
                "user_id": item.user_id,
                "product_id": item.product_id,
                "quantity": item.quantity,
                "created_at": item.created_at
            }
        return None
    finally:
        session.close()

async def db_add_cart_item(user_id: str, product_id: int, quantity: int = 1) -> Optional[str]:
    """Ajouter un item au panier"""
    session = get_db_session()
    if not session:
        return None
    try:
        item_id = str(uuid.uuid4())
        item = CartItemDB(id=item_id, user_id=user_id, product_id=product_id, quantity=quantity)
        session.add(item)
        session.commit()
        return item_id
    except Exception as e:
        session.rollback()
        logger.error(f"Error adding cart item: {e}")
        return None
    finally:
        session.close()

async def db_update_cart_item(item_id: str, user_id: str, quantity: int) -> bool:
    """Mettre à jour la quantité d'un item"""
    session = get_db_session()
    if not session:
        return False
    try:
        item = session.query(CartItemDB).filter(
            CartItemDB.id == item_id,
            CartItemDB.user_id == user_id
        ).first()
        if item:
            item.quantity = quantity
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        logger.error(f"Error updating cart item: {e}")
        return False
    finally:
        session.close()

async def db_update_cart_item_by_product(user_id: str, product_id: int, quantity: int) -> bool:
    """Mettre à jour la quantité par product_id"""
    session = get_db_session()
    if not session:
        return False
    try:
        item = session.query(CartItemDB).filter(
            CartItemDB.user_id == user_id,
            CartItemDB.product_id == product_id
        ).first()
        if item:
            item.quantity = quantity
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        logger.error(f"Error updating cart item: {e}")
        return False
    finally:
        session.close()

async def db_delete_cart_item(item_id: str, user_id: str) -> bool:
    """Supprimer un item du panier"""
    session = get_db_session()
    if not session:
        return False
    try:
        result = session.query(CartItemDB).filter(
            CartItemDB.id == item_id,
            CartItemDB.user_id == user_id
        ).delete()
        session.commit()
        return result > 0
    except Exception as e:
        session.rollback()
        logger.error(f"Error deleting cart item: {e}")
        return False
    finally:
        session.close()

async def db_clear_cart(user_id: str) -> bool:
    """Vider le panier d'un utilisateur"""
    session = get_db_session()
    if not session:
        return False
    try:
        session.query(CartItemDB).filter(CartItemDB.user_id == user_id).delete()
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        logger.error(f"Error clearing cart: {e}")
        return False
    finally:
        session.close()

# ============================================
# BLOG FUNCTIONS
# ============================================

async def db_get_blog_posts(limit: int = 100) -> List[Dict]:
    """Obtenir tous les articles de blog avec timeout protection"""
    session = get_db_session()
    if not session:
        logger.warning("⚠️ db_get_blog_posts: No database session available")
        return []
    try:
        posts = session.query(BlogPostDB).order_by(desc(BlogPostDB.created_at)).limit(limit).all()
        return [
            {
                "id": post.id,
                "title": post.title,
                "content": post.content,
                "excerpt": post.excerpt,
                "image": post.image,
                "author": post.author,
                "wix_post_id": post.wix_post_id,
                "published_to_wix": post.published_to_wix,
                "published_to_facebook": post.published_to_facebook,
                "pushed_to_wix": post.pushed_to_wix,
                "auto_generated": post.auto_generated,
                "category": post.category,
                "created_at": post.created_at
            }
            for post in posts
        ]
    except Exception as e:
        logger.error(f"❌ db_get_blog_posts error (returning empty): {e}")
        return []  # Retourne liste vide pour permettre fallback
    finally:
        session.close()

async def db_get_blog_post(post_id: str) -> Optional[Dict]:
    """Obtenir un article de blog par ID avec timeout protection"""
    session = get_db_session()
    if not session:
        logger.warning("⚠️ db_get_blog_post: No database session available")
        return None
    try:
        post = session.query(BlogPostDB).filter(BlogPostDB.id == post_id).first()
        if post:
            return {
                "id": post.id,
                "title": post.title,
                "content": post.content,
                "excerpt": post.excerpt,
                "image": post.image,
                "author": post.author,
                "wix_post_id": post.wix_post_id,
                "published_to_wix": post.published_to_wix,
                "published_to_facebook": post.published_to_facebook,
                "pushed_to_wix": post.pushed_to_wix,
                "auto_generated": post.auto_generated,
                "category": post.category,
                "created_at": post.created_at
            }
        return None
    except Exception as e:
        logger.error(f"❌ db_get_blog_post error (returning None): {e}")
        return None  # Retourne None pour permettre fallback vers articles par défaut
    finally:
        session.close()

async def db_get_blog_titles() -> List[str]:
    """Obtenir tous les titres de blog existants"""
    session = get_db_session()
    if not session:
        return []
    try:
        posts = session.query(BlogPostDB.title).all()
        return [post.title for post in posts]
    finally:
        session.close()

async def db_create_blog_post(post_data: Dict) -> Optional[str]:
    """Créer un nouvel article de blog"""
    session = get_db_session()
    if not session:
        return None
    try:
        post_id = post_data.get("id", str(uuid.uuid4()))
        post = BlogPostDB(
            id=post_id,
            title=post_data.get("title", ""),
            content=post_data.get("content", ""),
            excerpt=post_data.get("excerpt", ""),
            image=post_data.get("image"),
            author=post_data.get("author", "Luxura Distribution"),
            wix_post_id=post_data.get("wix_post_id"),
            published_to_wix=post_data.get("published_to_wix", False),
            published_to_facebook=post_data.get("published_to_facebook", False),
            pushed_to_wix=post_data.get("pushed_to_wix", False),
            auto_generated=post_data.get("auto_generated", False),
            category=post_data.get("category")
        )
        session.add(post)
        session.commit()
        return post_id
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating blog post: {e}")
        return None
    finally:
        session.close()

async def db_update_blog_post(post_id: str, updates: Dict) -> bool:
    """Mettre à jour un article de blog"""
    session = get_db_session()
    if not session:
        return False
    try:
        post = session.query(BlogPostDB).filter(BlogPostDB.id == post_id).first()
        if post:
            for key, value in updates.items():
                if hasattr(post, key):
                    setattr(post, key, value)
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        logger.error(f"Error updating blog post: {e}")
        return False
    finally:
        session.close()

async def db_delete_blog_post(post_id: str) -> bool:
    """Supprimer un article de blog"""
    session = get_db_session()
    if not session:
        return False
    try:
        result = session.query(BlogPostDB).filter(BlogPostDB.id == post_id).delete()
        session.commit()
        return result > 0
    except Exception as e:
        session.rollback()
        logger.error(f"Error deleting blog post: {e}")
        return False
    finally:
        session.close()

async def db_count_blog_posts(filter_dict: Dict = None) -> int:
    """Compter les articles de blog"""
    session = get_db_session()
    if not session:
        return 0
    try:
        query = session.query(BlogPostDB)
        if filter_dict:
            for key, value in filter_dict.items():
                if hasattr(BlogPostDB, key):
                    query = query.filter(getattr(BlogPostDB, key) == value)
        return query.count()
    finally:
        session.close()

# ============================================
# SEO LOG FUNCTIONS
# ============================================

async def db_create_seo_log(log_data: Dict) -> bool:
    """Créer un log SEO"""
    session = get_db_session()
    if not session:
        return False
    try:
        log = SEOLogDB(
            blog_id=log_data.get("blog_id"),
            title=log_data.get("title"),
            category=log_data.get("category"),
            status=log_data.get("status", "generated")
        )
        session.add(log)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating SEO log: {e}")
        return False
    finally:
        session.close()

async def db_get_seo_logs(limit: int = 10) -> List[Dict]:
    """Obtenir les logs SEO récents"""
    session = get_db_session()
    if not session:
        return []
    try:
        logs = session.query(SEOLogDB).order_by(desc(SEOLogDB.date)).limit(limit).all()
        return [
            {
                "id": log.id,
                "blog_id": log.blog_id,
                "title": log.title,
                "category": log.category,
                "date": log.date,
                "status": log.status
            }
            for log in logs
        ]
    finally:
        session.close()

# ============================================
# BACKLINK RUNS FUNCTIONS
# ============================================

async def db_create_backlink_run(run_data: Dict) -> bool:
    """Créer un log de backlink run"""
    session = get_db_session()
    if not session:
        return False
    try:
        run = BacklinkRunDB(
            directory=run_data.get("directory"),
            status=run_data.get("status"),
            message=run_data.get("message")
        )
        session.add(run)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating backlink run: {e}")
        return False
    finally:
        session.close()

async def db_get_backlink_runs(limit: int = 10) -> List[Dict]:
    """Obtenir les backlink runs récents"""
    session = get_db_session()
    if not session:
        return []
    try:
        runs = session.query(BacklinkRunDB).order_by(desc(BacklinkRunDB.date)).limit(limit).all()
        return [
            {
                "id": run.id,
                "directory": run.directory,
                "status": run.status,
                "message": run.message,
                "date": run.date
            }
            for run in runs
        ]
    finally:
        session.close()

# ============================================
# SALON FUNCTIONS
# ============================================

async def db_get_salons(city: str = None) -> List[Dict]:
    """Obtenir les salons"""
    session = get_db_session()
    if not session:
        return []
    try:
        query = session.query(SalonDB)
        if city:
            query = query.filter(SalonDB.city == city)
        salons = query.all()
        return [
            {
                "id": salon.id,
                "name": salon.name,
                "address": salon.address,
                "city": salon.city,
                "phone": salon.phone,
                "website": salon.website,
                "latitude": salon.latitude,
                "longitude": salon.longitude
            }
            for salon in salons
        ]
    finally:
        session.close()

# Initialize database on module load
init_db()
