"""
===============================================================================
FONCTION _build_description_html CORRIGÉE
===============================================================================

INSTRUCTIONS:
1. Ouvrir wix_seo_push.py sur Render
2. Rechercher "_build_description_html" (Ctrl+F)
3. SUPPRIMER les 2 fonctions _build_description_html existantes (elles sont dupliquées)
4. COLLER cette nouvelle version à la place
5. Sauvegarder et déployer

===============================================================================
"""


def _build_description_html(prod: Product) -> str:
    """
    Génère une description HTML SEO-optimisée pour Wix.
    
    Format:
    - HTML avec <p>, <br>, <strong>
    - "Qualité Russe exceptionnelle" inclus
    - "Luxura" en couleur or (#D4AF37)
    - Mots-clés SEO en gras
    - PAS d'emojis
    """
    product_type, series, _prefix = _infer_type_and_series(prod)
    color_code = _extract_color_code(prod) or ""
    color = _color_meta(color_code)
    luxe_name = color.get("luxe", color_code)
    
    # Luxura en or
    luxura = '<span style="color:#D4AF37;font-weight:bold;">Luxura</span>'
    
    # Bloc SEO Local (commun à toutes les catégories)
    seo_local = f"""<p><strong>Disponible au Québec:</strong><br>
<strong>Rajouts cheveux</strong> Québec | <strong>Rallonges capillaires</strong> Montréal | <strong>Volume capillaire</strong> Laval<br>
<strong>Cheveux naturels Remy</strong> Lévis | <strong>Extensions professionnelles</strong> Trois-Rivières | <strong>Pose extensions</strong> Beauce</p>

<p>{luxura} Distribution – Leader des <strong>extensions capillaires professionnelles</strong> au Québec et au Canada.</p>"""

    # ===== HALO =====
    if product_type == "Halo":
        return f"""<p><strong>Extensions Halo {series}</strong> – Volume instantané sans engagement par {luxura}.</p>

<p><strong>Qualité Russe exceptionnelle</strong> – Les cheveux les plus fins et soyeux au monde.</p>

<p><strong>Concept unique:</strong><br>
• Fil invisible ajustable qui repose sur votre tête<br>
• Aucune fixation permanente – 100% réversible<br>
• Application en moins de 2 minutes<br>
• Retrait instantané sans aide professionnelle</p>

<p><strong>Qualité Premium:</strong><br>
• 100% <strong>cheveux humains vierges Remy</strong><br>
• Cuticules intactes alignées dans le même sens<br>
• Série {series} – Collection professionnelle {luxura}<br>
• Teinte: <strong>{luxe_name} #{color_code}</strong></p>

<p><strong>Avantages uniques:</strong><br>
• Zéro dommage aux <strong>cheveux naturels</strong><br>
• Parfait pour usage quotidien ou occasionnel<br>
• Idéal pour cheveux fins ou fragiles<br>
• Durée de vie: 12 mois et plus avec bon entretien</p>

<p><strong>Application:</strong> Auto-application – Aucune aide requise</p>

{seo_local}"""

    # ===== GENIUS =====
    elif product_type == "Genius":
        return f"""<p><strong>Extensions Genius Weft {series}</strong> – Trames ultra-fines invisibles par {luxura}.</p>

<p><strong>Qualité Russe exceptionnelle</strong> – Les cheveux les plus fins et soyeux au monde.</p>

<p><strong>Technologie exclusive:</strong><br>
• Fabrication sans aucune couture (contrairement aux hand-tied)<br>
• Zéro retour de cheveux – pas de "moustache" irritante<br>
• Kératine italienne anti-allergène ultra-résistante<br>
• Trame 40% plus fine que les extensions traditionnelles</p>

<p><strong>Qualité Premium:</strong><br>
• 100% <strong>cheveux humains vierges Remy</strong><br>
• Cuticules intactes alignées dans le même sens<br>
• Série {series} – Collection signature {luxura}<br>
• Teinte: <strong>{luxe_name} #{color_code}</strong></p>

<p><strong>Avantages uniques:</strong><br>
• Confort maximal – plus souple que les trames cousues<br>
• Peut être coupée n'importe où sans effilochage<br>
• Invisible même sur cheveux fins<br>
• Durée de vie: 12-18 mois avec bon entretien</p>

<p><strong>Application:</strong> Pose professionnelle (micro-anneaux, bandes ou couture)</p>

{seo_local}"""

    # ===== TAPE =====
    elif product_type == "Tape":
        return f"""<p><strong>Extensions Bande Adhésive {series}</strong> – Pose rapide et confort absolu par {luxura}.</p>

<p><strong>Qualité Russe exceptionnelle</strong> – Les cheveux les plus fins et soyeux au monde.</p>

<p><strong>Technologie adhésive premium:</strong><br>
• Bandes ultra-fines et discrètes<br>
• Adhésif médical hypoallergénique<br>
• Pose en sandwich – tenue sécurisée<br>
• Réutilisables jusqu'à 3 poses</p>

<p><strong>Qualité Premium:</strong><br>
• 100% <strong>cheveux humains vierges Remy</strong><br>
• Cuticules intactes alignées dans le même sens<br>
• Série {series} – Collection professionnelle {luxura}<br>
• Teinte: <strong>{luxe_name} #{color_code}</strong></p>

<p><strong>Avantages uniques:</strong><br>
• Pose rapide – environ 45 minutes en salon<br>
• Confortable et légère au quotidien<br>
• Invisible à la racine<br>
• Durée de vie: 8-12 semaines par pose, 12 mois total</p>

<p><strong>Application:</strong> Pose professionnelle en salon recommandée</p>

{seo_local}"""

    # ===== I-TIP =====
    elif product_type == "I-Tip":
        return f"""<p><strong>Extensions I-Tip {series}</strong> – Précision et personnalisation par {luxura}.</p>

<p><strong>Qualité Russe exceptionnelle</strong> – Les cheveux les plus fins et soyeux au monde.</p>

<p><strong>Technologie micro-anneaux:</strong><br>
• Pose mèche par mèche ultra-précise<br>
• Anneaux micro-silicone – zéro chaleur, zéro colle<br>
• Ajustement personnalisé à votre chevelure<br>
• Retrait facile et sans dommage</p>

<p><strong>Qualité Premium:</strong><br>
• 100% <strong>cheveux humains vierges Remy</strong><br>
• Kératine italienne premium<br>
• Série {series} – Collection professionnelle {luxura}<br>
• Teinte: <strong>{luxe_name} #{color_code}</strong></p>

<p><strong>Avantages uniques:</strong><br>
• Résultat le plus naturel possible<br>
• Idéal pour ajouts de <strong>volume capillaire</strong> ciblés<br>
• Parfait pour cheveux fins<br>
• Durée de vie: 4-6 mois avec entretien</p>

<p><strong>Application:</strong> Pose professionnelle en salon (2-3 heures)</p>

{seo_local}"""

    # ===== DÉFAUT (Essentiels ou autre) =====
    else:
        return f"""<p><strong>Produit Professionnel</strong> par {luxura}.</p>

<p><strong>Qualité Premium:</strong><br>
• Produit de qualité salon<br>
• Testé et approuvé par les professionnels<br>
• Collection {luxura}</p>

{seo_local}"""
