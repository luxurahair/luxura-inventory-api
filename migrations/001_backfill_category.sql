-- Migration: Backfill product.category depuis options.categories
-- Exécuter dans Supabase SQL Editor

-- 1. S'assurer que la colonne existe
ALTER TABLE public.product
ADD COLUMN IF NOT EXISTS category VARCHAR NULL;

-- 2. Créer un index pour améliorer les performances des requêtes par catégorie
CREATE INDEX IF NOT EXISTS idx_product_category ON public.product(category);

-- 3. Backfill: extraire les catégories du JSON et les mettre dans la colonne
UPDATE public.product
SET category = subquery.cat_text
FROM (
    SELECT 
        id,
        NULLIF(
            ARRAY_TO_STRING(
                ARRAY(
                    SELECT jsonb_array_elements_text(COALESCE(options->'categories', '[]'::jsonb))
                ),
                ', '
            ),
            ''
        ) as cat_text
    FROM public.product
) as subquery
WHERE public.product.id = subquery.id
  AND (public.product.category IS NULL OR BTRIM(public.product.category) = '');

-- 4. Vérifier le résultat
SELECT 
    COUNT(*) as total,
    COUNT(category) as with_category,
    COUNT(*) - COUNT(category) as without_category
FROM public.product;
