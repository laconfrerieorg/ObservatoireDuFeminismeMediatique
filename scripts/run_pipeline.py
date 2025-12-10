#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script d'orchestration pour exécuter le pipeline complet.
Exécute tous les scripts dans l'ordre.
"""

import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
SCRIPTS_DIR = BASE_DIR / "scripts"


def run_script(script_name: str, description: str) -> bool:
    """Exécute un script Python et retourne True si succès."""
    print(f"\n{'='*60}")
    print(f"🔄 {description}")
    print(f"{'='*60}\n")
    
    script_path = SCRIPTS_DIR / script_name
    
    if not script_path.exists():
        print(f"❌ Script introuvable: {script_path}")
        return False
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(BASE_DIR),
            check=True
        )
        print(f"\n✅ {description} terminé avec succès")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Erreur lors de l'exécution de {script_name}: {e}")
        return False
    except KeyboardInterrupt:
        print(f"\n⚠️  Interruption par l'utilisateur")
        return False


def main():
    """Exécute le pipeline complet."""
    print("🚀 Démarrage du pipeline complet de l'Observatoire des médias")
    print("=" * 60)
    
    steps = [
        ("collect_urls.py", "Collecte des URLs"),
        ("fetch_articles.py", "Téléchargement des articles"),
        ("parse_articles.py", "Parsing des articles"),
        ("analyze_articles.py", "Analyse et scoring"),
        ("build_stats.py", "Génération des statistiques"),
    ]
    
    success_count = 0
    failed_steps = []
    
    for script_name, description in steps:
        if run_script(script_name, description):
            success_count += 1
        else:
            failed_steps.append(description)
            # Demander si on continue malgré l'erreur
            response = input(f"\n⚠️  Erreur à l'étape '{description}'. Continuer ? (o/N): ")
            if response.lower() != 'o':
                print("\n❌ Pipeline interrompu par l'utilisateur")
                break
    
    print(f"\n{'='*60}")
    print("📊 Résumé du pipeline")
    print(f"{'='*60}")
    print(f"✅ Étapes réussies: {success_count}/{len(steps)}")
    
    if failed_steps:
        print(f"❌ Étapes échouées: {', '.join(failed_steps)}")
    else:
        print("🎉 Pipeline terminé avec succès !")
        print("\n💡 Pour visualiser les résultats, lancez:")
        print("   python app/api.py")
        print("   Puis ouvrez http://localhost:5000 dans votre navigateur")


if __name__ == "__main__":
    main()

