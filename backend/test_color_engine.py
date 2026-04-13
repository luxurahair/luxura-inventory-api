"""
Test complet du Color Engine
Objectif: Vérifier que les couleurs changent vraiment
"""

import numpy as np
import cv2
from PIL import Image
import os
import sys

# Ajouter le chemin du backend
sys.path.insert(0, '/app/backend')

from color_engine_api import (
    recolor_with_reference,
    extract_dominant_color_hsv,
    improve_hair_mask
)

def test_color_extraction():
    """Test 1: Vérifier que les couleurs sont bien extraites des références"""
    print("\n" + "="*60)
    print("TEST 1: Extraction des couleurs de référence")
    print("="*60)
    
    colors_to_test = ["1", "2", "6", "22", "1B", "24"]
    
    for code in colors_to_test:
        # Chercher le fichier de référence
        import glob
        pattern = f"/app/backend/luxura_images/color_library/reference/*_{code}.jpg"
        matches = glob.glob(pattern)
        
        if not matches:
            pattern = f"/app/backend/luxura_images/color_library/reference/*{code}*.jpg"
            matches = glob.glob(pattern)
        
        if matches:
            ref_path = matches[0]
            ref_img = np.array(Image.open(ref_path).convert('RGB'))
            h, s, v = extract_dominant_color_hsv(ref_img)
            print(f"  #{code}: H={h:5.1f}, S={s:5.1f}, V={v:5.1f} - {os.path.basename(ref_path)}")
        else:
            print(f"  #{code}: ❌ Fichier non trouvé")

def test_color_difference():
    """Test 2: Vérifier que les couleurs de référence sont différentes"""
    print("\n" + "="*60)
    print("TEST 2: Différence entre couleurs")
    print("="*60)
    
    # Charger quelques références
    import glob
    
    colors = {}
    for code in ["1", "2", "6", "22", "24"]:
        pattern = f"/app/backend/luxura_images/color_library/reference/*_{code}.jpg"
        matches = glob.glob(pattern)
        if matches:
            ref_img = np.array(Image.open(matches[0]).convert('RGB'))
            h, s, v = extract_dominant_color_hsv(ref_img)
            colors[code] = (h, s, v)
    
    # Comparer les couleurs
    codes = list(colors.keys())
    for i, c1 in enumerate(codes):
        for c2 in codes[i+1:]:
            h1, s1, v1 = colors[c1]
            h2, s2, v2 = colors[c2]
            h_diff = abs(h1 - h2)
            s_diff = abs(s1 - s2)
            v_diff = abs(v1 - v2)
            print(f"  #{c1} vs #{c2}: ΔH={h_diff:5.1f}, ΔS={s_diff:5.1f}, ΔV={v_diff:5.1f}")

def test_recoloring():
    """Test 3: Test de recolorisation réelle"""
    print("\n" + "="*60)
    print("TEST 3: Recolorisation")
    print("="*60)
    
    # Charger le gabarit par défaut
    gabarit_path = "/app/backend/templates/gabarit_genius.jpg"
    if not os.path.exists(gabarit_path):
        print("❌ Gabarit non trouvé!")
        return
    
    gabarit = np.array(Image.open(gabarit_path).convert('RGB'))
    print(f"  Gabarit chargé: {gabarit.shape}")
    
    # Extraire la couleur du gabarit
    gab_h, gab_s, gab_v = extract_dominant_color_hsv(gabarit)
    print(f"  Couleur gabarit: H={gab_h:.1f}, S={gab_s:.1f}, V={gab_v:.1f}")
    
    # Tester avec différentes couleurs
    import glob
    test_colors = ["1", "22"]  # Noir vs Blond - très différent
    
    output_dir = "/tmp/color_engine_test"
    os.makedirs(output_dir, exist_ok=True)
    
    for code in test_colors:
        pattern = f"/app/backend/luxura_images/color_library/reference/*_{code}.jpg"
        matches = glob.glob(pattern)
        
        if matches:
            ref_path = matches[0]
            ref_img = np.array(Image.open(ref_path).convert('RGB'))
            
            ref_h, ref_s, ref_v = extract_dominant_color_hsv(ref_img)
            print(f"\n  Recolorisation vers #{code} (H={ref_h:.1f}, S={ref_s:.1f}, V={ref_v:.1f})")
            
            # Recoloriser
            result, mask = recolor_with_reference(gabarit, ref_img, blend=0.9)
            
            # Extraire la couleur du résultat
            result_h, result_s, result_v = extract_dominant_color_hsv(result)
            print(f"  Résultat: H={result_h:.1f}, S={result_s:.1f}, V={result_v:.1f}")
            
            # Calculer le changement
            h_change = abs(result_h - gab_h)
            s_change = abs(result_s - gab_s)
            print(f"  Changement: ΔH={h_change:.1f}, ΔS={s_change:.1f}")
            
            # Sauvegarder
            output_path = f"{output_dir}/result_{code}.png"
            Image.fromarray(result).save(output_path)
            print(f"  Sauvegardé: {output_path}")

def analyze_problem():
    """Analyse du problème"""
    print("\n" + "="*60)
    print("ANALYSE DU PROBLÈME")
    print("="*60)
    
    # Vérifier les images de référence
    import glob
    
    ref_dir = "/app/backend/luxura_images/color_library/reference"
    files = glob.glob(f"{ref_dir}/*.jpg")
    
    print(f"\n  Total fichiers référence: {len(files)}")
    
    # Vérifier quelques images
    print("\n  Échantillon d'images:")
    for f in files[:5]:
        img = Image.open(f)
        print(f"    {os.path.basename(f)}: {img.size}, mode={img.mode}")

if __name__ == "__main__":
    print("="*60)
    print("TEST COLOR ENGINE - DIAGNOSTIC COMPLET")
    print("="*60)
    
    test_color_extraction()
    test_color_difference()
    test_recoloring()
    analyze_problem()
    
    print("\n" + "="*60)
    print("TESTS TERMINÉS")
    print("="*60)
