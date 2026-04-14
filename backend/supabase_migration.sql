-- LUXURA SUPABASE MIGRATION
-- Exécutez ce script dans Supabase SQL Editor

-- Table des utilisateurs
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    picture TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table des sessions
CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    session_token TEXT UNIQUE NOT NULL,
    user_id TEXT REFERENCES users(user_id) ON DELETE CASCADE,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table du panier
CREATE TABLE IF NOT EXISTS cart_items (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id TEXT REFERENCES users(user_id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL,
    quantity INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table des articles de blog
CREATE TABLE IF NOT EXISTS blog_posts (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    excerpt TEXT,
    image TEXT,
    author TEXT DEFAULT 'Luxura Distribution',
    wix_post_id TEXT,
    published_to_wix BOOLEAN DEFAULT FALSE,
    published_to_facebook BOOLEAN DEFAULT FALSE,
    category TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table des logs SEO
CREATE TABLE IF NOT EXISTS seo_generation_log (
    id SERIAL PRIMARY KEY,
    blog_id TEXT,
    title TEXT,
    category TEXT,
    generated_at TIMESTAMPTZ DEFAULT NOW(),
    status TEXT DEFAULT 'generated'
);

-- Index pour performance
CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_user_sessions_user ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_cart_items_user ON cart_items(user_id);
CREATE INDEX IF NOT EXISTS idx_blog_posts_created ON blog_posts(created_at DESC);

-- Permissions RLS (Row Level Security) - optionnel
-- ALTER TABLE users ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE cart_items ENABLE ROW LEVEL SECURITY;
