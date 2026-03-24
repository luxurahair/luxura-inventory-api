"""
=============================================================================
FONCTION DE GÉNÉRATION DE DESCRIPTIONS SEO - À INTÉGRER DANS wix_seo_push.py
=============================================================================

Instructions:
1. Ouvrir votre fichier wix_seo_push.py sur Render
2. Rechercher la fonction generate_seo_description() existante
3. REMPLACER cette fonction par celle ci-dessous
4. Sauvegarder et déployer

Format des descriptions:
- HTML avec <p>, <br>, <strong>
- "Qualité Russe exceptionnelle" inclus
- "Luxura" en couleur or (#c9a050)
- Mots-clés SEO en gras
- PAS d'emojis
=============================================================================
"""

def generate_seo_description(category: str, color_name: str, color_code: str) -> str:
    """
    Génère une description SEO optimisée pour Wix.
    
    Args:
        category: 'genius', 'halo', 'tape', 'i-tip'
        color_name: Nom luxe de la couleur (ex: "Châtaigne Lumière")
        color_code: Code couleur (ex: "#3/3T24")
    
    Returns:
        Description HTML formatée pour Wix
    """
    
    # Marque Luxura en or
    LUXURA = '<span style="color:#c9a050;font-weight:bold;">Luxura</span>'
    
    # Descriptions par catégorie
    descriptions = {
        "genius": f"""<p><strong>Extensions Genius Vivian</strong> – La trame invisible révolutionnaire par {LUXURA}.</p>

<p><strong>Qualité Russe exceptionnelle</strong> – Cheveux 100% naturels vierges Remy, cuticules intactes et alignées pour un rendu ultra-naturel et une durabilité supérieure.</p>

<p><strong>Technologie exclusive :</strong><br>
• Fabrication sans couture (contrairement aux hand-tied)<br>
• Zéro retour de cheveux – pas de "moustache" irritante<br>
• Kératine italienne anti-allergène ultra-résistante<br>
• Trame 40% plus fine que les extensions traditionnelles</p>

<p><strong>Teinte :</strong> {color_name} {color_code}</p>

<p><strong>Avantages uniques :</strong><br>
• Confort maximal – plus souple que les trames cousues<br>
• Peut être coupée n'importe où sans effilochage<br>
• Invisible même sur cheveux fins<br>
• Durée de vie : 12 mois et plus avec bon entretien</p>

<p><strong>Application :</strong> Pose professionnelle (micro-anneaux, bandes ou couture)</p>

<p><strong>Mots-clés :</strong> <strong>rajouts cheveux</strong>, <strong>extensions capillaires</strong>, <strong>volume capillaire</strong>, <strong>rallonges cheveux naturels</strong>, <strong>extensions cheveux Québec</strong></p>

<p>{LUXURA} Distribution – Leader des <strong>extensions professionnelles</strong> au Québec et au Canada.</p>""",

        "halo": f"""<p><strong>Extensions Halo Everly</strong> – Volume instantané sans engagement par {LUXURA}.</p>

<p><strong>Qualité Russe exceptionnelle</strong> – Cheveux 100% naturels vierges Remy, cuticules intactes pour un mouvement naturel et une brillance incomparable.</p>

<p><strong>Concept unique :</strong><br>
• Fil invisible ajustable qui repose sur votre tête<br>
• Aucune fixation permanente – 100% réversible<br>
• Application en moins de 2 minutes<br>
• Retrait instantané sans aide professionnelle</p>

<p><strong>Teinte :</strong> {color_name} {color_code}</p>

<p><strong>Avantages uniques :</strong><br>
• Zéro dommage aux cheveux naturels<br>
• Parfait pour usage quotidien ou occasionnel<br>
• Idéal pour cheveux fins ou fragiles<br>
• Durée de vie : 12 mois et plus avec bon entretien</p>

<p><strong>Application :</strong> Auto-application – Aucune aide requise</p>

<p><strong>Mots-clés :</strong> <strong>rajouts cheveux</strong>, <strong>extensions capillaires</strong>, <strong>volume capillaire</strong>, <strong>halo extensions</strong>, <strong>extensions cheveux Québec</strong></p>

<p>{LUXURA} Distribution – <strong>Extensions professionnelles</strong> haut de gamme.</p>""",

        "tape": f"""<p><strong>Extensions Bande Adhésive Aurora</strong> – Pose rapide et confort absolu par {LUXURA}.</p>

<p><strong>Qualité Russe exceptionnelle</strong> – Cheveux 100% naturels vierges Remy, cuticules intactes et alignées pour une fusion parfaite avec vos cheveux.</p>

<p><strong>Technologie adhésive premium :</strong><br>
• Bandes ultra-fines et discrètes<br>
• Adhésif médical hypoallergénique<br>
• Pose en sandwich – tenue sécurisée<br>
• Réutilisables jusqu'à 3 poses</p>

<p><strong>Teinte :</strong> {color_name} {color_code}</p>

<p><strong>Avantages uniques :</strong><br>
• Pose rapide – environ 45 minutes en salon<br>
• Confortable et légère au quotidien<br>
• Invisible à la racine<br>
• Durée de vie : 8-12 semaines par pose</p>

<p><strong>Application :</strong> Pose professionnelle en salon recommandée</p>

<p><strong>Mots-clés :</strong> <strong>tape extensions</strong>, <strong>extensions adhésives</strong>, <strong>rajouts cheveux</strong>, <strong>extensions capillaires</strong>, <strong>extensions cheveux Québec</strong></p>

<p>{LUXURA} Distribution – <strong>Extensions professionnelles</strong> qualité salon.</p>""",

        "i-tip": f"""<p><strong>Extensions I-Tip Eleanor</strong> – Précision et personnalisation par {LUXURA}.</p>

<p><strong>Qualité Russe exceptionnelle</strong> – Cheveux 100% naturels vierges Remy, cuticules intactes pour une intégration parfaite mèche par mèche.</p>

<p><strong>Technologie micro-anneaux :</strong><br>
• Pose mèche par mèche ultra-précise<br>
• Anneaux micro-silicone – zéro chaleur, zéro colle<br>
• Ajustement personnalisé à votre chevelure<br>
• Retrait facile et sans dommage</p>

<p><strong>Teinte :</strong> {color_name} {color_code}</p>

<p><strong>Avantages uniques :</strong><br>
• Résultat le plus naturel possible<br>
• Idéal pour ajouts de volume ciblés<br>
• Parfait pour cheveux fins<br>
• Durée de vie : 4-6 mois avec entretien</p>

<p><strong>Application :</strong> Pose professionnelle en salon (2-3 heures)</p>

<p><strong>Mots-clés :</strong> <strong>i-tip extensions</strong>, <strong>micro-anneaux</strong>, <strong>rajouts cheveux</strong>, <strong>extensions capillaires</strong>, <strong>extensions cheveux Québec</strong></p>

<p>{LUXURA} Distribution – <strong>Extensions professionnelles</strong> de précision.</p>"""
    }
    
    return descriptions.get(category, descriptions["genius"])


# =============================================================================
# COMMENT INTÉGRER DANS wix_seo_push.py :
# =============================================================================
#
# 1. Trouvez la fonction existante qui génère les descriptions
#    (probablement appelée generate_description, generate_seo_description, 
#    ou build_description)
#
# 2. Remplacez-la par la fonction ci-dessus
#
# 3. Dans la partie du code qui appelle cette fonction, assurez-vous 
#    de passer les bons paramètres:
#
#    description = generate_seo_description(
#        category=product_category,      # 'genius', 'halo', 'tape', 'i-tip'
#        color_name=luxe_color_name,     # 'Châtaigne Lumière'
#        color_code=color_code           # '#3/3T24'
#    )
#
# 4. Sauvegardez et redéployez sur Render
#
# =============================================================================
