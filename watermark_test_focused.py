#!/usr/bin/env python3
"""
Focused test for LUXURA watermark service
Tests only the watermark functionality as requested in the review
"""

import requests
import json
import sys
import asyncio
import os
from datetime import datetime

# Add backend to path
sys.path.append('/app/backend')

# Base URL for the API
BASE_URL = "https://hair-extensions-shop.preview.emergentagent.com/api"

def test_watermark_unit():
    """Test unitaire du module watermark comme demandé"""
    print("🧪 Test unitaire du module watermark")
    print("-" * 40)
    
    try:
        from app.services.watermark import process_image_with_watermark
        
        # Test avec une image Unsplash comme spécifié
        url = "https://images.unsplash.com/photo-1496440737103-cd596325d314?w=800"
        result = asyncio.run(process_image_with_watermark(url))
        
        if result and isinstance(result, bytes):
            size_bytes = len(result)
            size_kb = size_bytes // 1024
            print(f"✅ Résultat: {size_bytes} bytes ({size_kb}KB)")
            
            if size_bytes > 100000:  # > 100KB comme demandé
                print(f"✅ Taille OK: {size_kb}KB > 100KB")
                return True
            else:
                print(f"❌ Taille insuffisante: {size_kb}KB < 100KB")
                return False
        else:
            print(f"❌ ECHEC: résultat invalide {type(result)}")
            return False
            
    except Exception as e:
        print(f"❌ ECHEC: {str(e)}")
        return False

def test_content_pending():
    """Test de l'endpoint /api/content/pending"""
    print("\n🔍 Test endpoint /api/content/pending")
    print("-" * 40)
    
    try:
        response = requests.get(f"{BASE_URL}/content/pending")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Retourne une liste des posts en attente: {data.get('pending_count', 0)} posts")
            return True
        else:
            print(f"❌ HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        return False

def test_approval_flow():
    """Test de l'endpoint /api/content/test-approval-flow"""
    print("\n🚀 Test endpoint /api/content/test-approval-flow")
    print("-" * 40)
    
    try:
        response = requests.post(f"{BASE_URL}/content/test-approval-flow")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                post_id = data.get("post_id")
                approve_url = data.get("approve_url")
                reject_url = data.get("reject_url")
                
                print(f"✅ Post de test créé: {post_id}")
                print(f"✅ URL approbation: {approve_url}")
                print(f"✅ URL rejet: {reject_url}")
                return True
            else:
                print(f"❌ Échec: {data}")
                return False
        else:
            print(f"❌ HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        return False

def test_watermark_format():
    """Vérifier que le format est JPEG"""
    print("\n📷 Test format JPEG du watermark")
    print("-" * 40)
    
    try:
        from app.services.watermark import process_image_with_watermark
        
        url = "https://images.unsplash.com/photo-1496440737103-cd596325d314?w=800"
        result = asyncio.run(process_image_with_watermark(url))
        
        if result:
            # Vérifier les magic bytes JPEG
            if result.startswith(b'\xff\xd8\xff'):
                print("✅ Format JPEG confirmé (magic bytes FF D8 FF)")
                return True
            else:
                print(f"❌ Format incorrect: {result[:10]}")
                return False
        else:
            print("❌ Pas de résultat")
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        return False

def main():
    """Exécute tous les tests demandés"""
    print("🏷️ TESTS WATERMARK LUXURA DORÉ")
    print("=" * 50)
    
    results = []
    
    # Test 1: Module watermark
    results.append(test_watermark_unit())
    
    # Test 2: Endpoint pending
    results.append(test_content_pending())
    
    # Test 3: Endpoint test-approval-flow
    results.append(test_approval_flow())
    
    # Test 4: Format JPEG
    results.append(test_watermark_format())
    
    # Résumé
    print("\n" + "=" * 50)
    print("📊 RÉSULTATS ATTENDUS")
    print("=" * 50)
    
    tests = [
        "✅ Module watermark importable et fonctionnel",
        "✅ Images watermarkées générées correctement (>100KB)",
        "✅ Endpoints content accessibles", 
        "✅ Flux d'approbation prêt"
    ]
    
    passed = sum(results)
    total = len(results)
    
    for i, test in enumerate(tests):
        status = "✅" if results[i] else "❌"
        print(f"{status} {test.split(' ', 1)[1]}")
    
    print(f"\n🎯 SCORE: {passed}/{total} tests réussis")
    
    if passed == total:
        print("🎉 TOUS LES TESTS PASSENT - WATERMARK LUXURA PRÊT!")
    else:
        print("⚠️ Certains tests échouent - Vérifier l'implémentation")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)