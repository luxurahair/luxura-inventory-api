#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# 🔧 SETUP EMERGENT ENV - Copie les secrets vers l'environnement Emergent
# ═══════════════════════════════════════════════════════════════
# Usage: ./scripts/setup_emergent_env.sh
# ═══════════════════════════════════════════════════════════════

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SECRETS_FILE="$PROJECT_ROOT/.secrets.env"

echo "═══════════════════════════════════════════════════════════════"
echo "🔧 LUXURA ENV SETUP"
echo "═══════════════════════════════════════════════════════════════"

# Vérifier que le fichier secrets existe
if [ ! -f "$SECRETS_FILE" ]; then
    echo "❌ Fichier .secrets.env non trouvé!"
    echo "   Créez-le avec: cp .env.example .secrets.env"
    exit 1
fi

echo "✅ Fichier secrets trouvé: $SECRETS_FILE"
echo ""

# Copier vers /app/backend/.env pour Emergent
if [ -d "/app/backend" ]; then
    echo "📋 Copie vers /app/backend/.env..."
    cp "$SECRETS_FILE" /app/backend/.env
    echo "   ✅ /app/backend/.env mis à jour"
fi

# Copier aussi dans le dossier local backend
if [ -d "$PROJECT_ROOT/backend" ]; then
    echo "📋 Copie vers backend/.env local..."
    cp "$SECRETS_FILE" "$PROJECT_ROOT/backend/.env"
    echo "   ✅ backend/.env mis à jour"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "📊 Variables chargées:"
echo "═══════════════════════════════════════════════════════════════"
grep -E "^[A-Z]" "$SECRETS_FILE" | cut -d= -f1 | while read var; do
    echo "   ✅ $var"
done

echo ""
echo "🎉 Setup terminé! Redémarrez le backend:"
echo "   sudo supervisorctl restart backend"
