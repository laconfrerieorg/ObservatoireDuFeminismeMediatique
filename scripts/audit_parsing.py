#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script d'audit du parsing des articles.
Compare un échantillon d'articles parsés avec les articles originaux pour détecter les erreurs.
"""

import os
import sys
import csv
import random
from pathlib import Path
from typing import List, Dict
import webbrowser

sys.path.insert(0, str(Path(__file__).parent.parent))


class ParsingAuditor:
    """Audite la qualité du parsing des articles."""
    
    def __init__(self, sample_size: int = 20):
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / "data"
        self.articles_file = self.data_dir / "articles_clean.csv"
        self.sample_size = sample_size
    
    def load_articles(self) -> List[Dict]:
        """Charge tous les articles parsés."""
        if not self.articles_file.exists():
            print("❌ Fichier articles_clean.csv non trouvé")
            return []
        
        articles = []
        with open(self.articles_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                articles.append(row)
        
        return articles
    
    def sample_articles(self, articles: List[Dict]) -> List[Dict]:
        """Échantillonne aléatoirement des articles."""
        if len(articles) <= self.sample_size:
            return articles
        
        return random.sample(articles, self.sample_size)
    
    def generate_audit_report(self, sample: List[Dict]) -> str:
        """Génère un rapport d'audit."""
        report = []
        report.append("=" * 80)
        report.append("📋 RAPPORT D'AUDIT DU PARSING")
        report.append("=" * 80)
        report.append(f"\n📊 Échantillon analysé : {len(sample)} articles")
        report.append(f"📅 Date de l'audit : {Path(__file__).stat().st_mtime}")
        report.append("\n" + "-" * 80)
        report.append("\n📝 INSTRUCTIONS :")
        report.append("1. Pour chaque article, ouvrez l'URL dans votre navigateur")
        report.append("2. Comparez le texte extrait avec le texte de l'article original")
        report.append("3. Notez si le parsing est correct (✅) ou incorrect (❌)")
        report.append("4. Si incorrect, notez ce qui manque ou est incorrect")
        report.append("\n" + "-" * 80)
        report.append("\n")
        
        for i, article in enumerate(sample, 1):
            url = article.get('url', '')
            title = article.get('title', 'Sans titre')
            text_length = article.get('text_length', 0)
            text_preview = article.get('text', '')[:200] + "..." if len(article.get('text', '')) > 200 else article.get('text', '')
            
            report.append(f"\n{'=' * 80}")
            report.append(f"ARTICLE {i}/{len(sample)}")
            report.append(f"{'=' * 80}")
            report.append(f"📰 Titre : {title}")
            report.append(f"🔗 URL : {url}")
            report.append(f"📏 Longueur du texte extrait : {text_length} caractères")
            report.append(f"\n📄 Aperçu du texte extrait (200 premiers caractères) :")
            report.append(f"   {text_preview}")
            report.append(f"\n✅ Parsing correct ? [ ] Oui  [ ] Non")
            report.append(f"📝 Commentaires :")
            report.append(f"   ")
            report.append("")
        
        report.append("\n" + "=" * 80)
        report.append("FIN DU RAPPORT")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def save_report(self, report: str):
        """Sauvegarde le rapport dans un fichier."""
        report_file = self.data_dir / "audit_parsing_report.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"✅ Rapport sauvegardé : {report_file}")
        return report_file
    
    def generate_html_report(self, sample: List[Dict]) -> str:
        """Génère un rapport HTML interactif."""
        html = []
        html.append("<!DOCTYPE html>")
        html.append("<html lang='fr'>")
        html.append("<head>")
        html.append("    <meta charset='UTF-8'>")
        html.append("    <meta name='viewport' content='width=device-width, initial-scale=1.0'>")
        html.append("    <title>Audit du Parsing</title>")
        html.append("    <style>")
        html.append("        body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }")
        html.append("        .article { border: 1px solid #ddd; margin: 20px 0; padding: 20px; border-radius: 8px; }")
        html.append("        .article h3 { margin-top: 0; color: #333; }")
        html.append("        .url { color: #0066cc; word-break: break-all; }")
        html.append("        .preview { background: #f5f5f5; padding: 10px; border-radius: 4px; margin: 10px 0; font-size: 0.9em; }")
        html.append("        .stats { color: #666; font-size: 0.9em; }")
        html.append("        .checkboxes { margin: 10px 0; }")
        html.append("        .checkboxes label { margin-right: 20px; }")
        html.append("        textarea { width: 100%; min-height: 60px; margin-top: 10px; }")
        html.append("        button { background: #0066cc; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }")
        html.append("        button:hover { background: #0052a3; }")
        html.append("        .header { background: #f0f0f0; padding: 20px; border-radius: 8px; margin-bottom: 20px; }")
        html.append("    </style>")
        html.append("</head>")
        html.append("<body>")
        html.append("    <div class='header'>")
        html.append("        <h1>📋 Audit du Parsing des Articles</h1>")
        html.append(f"        <p>Échantillon analysé : {len(sample)} articles</p>")
        html.append("        <p><strong>Instructions :</strong> Pour chaque article, ouvrez l'URL, comparez avec le texte extrait, et notez si le parsing est correct.</p>")
        html.append("    </div>")
        
        for i, article in enumerate(sample, 1):
            url = article.get('url', '')
            title = article.get('title', 'Sans titre')
            text_length = article.get('text_length', 0)
            text_preview = article.get('text', '')[:500] + "..." if len(article.get('text', '')) > 500 else article.get('text', '')
            
            html.append(f"    <div class='article'>")
            html.append(f"        <h3>Article {i}/{len(sample)} : {title}</h3>")
            html.append(f"        <p><strong>URL :</strong> <a href='{url}' target='_blank' class='url'>{url}</a></p>")
            html.append(f"        <p class='stats'>Longueur du texte extrait : {text_length} caractères</p>")
            html.append(f"        <div class='preview'><strong>Aperçu du texte extrait :</strong><br>{text_preview}</div>")
            html.append(f"        <div class='checkboxes'>")
            html.append(f"            <label><input type='radio' name='result_{i}' value='correct'> ✅ Parsing correct</label>")
            html.append(f"            <label><input type='radio' name='result_{i}' value='incorrect'> ❌ Parsing incorrect</label>")
            html.append(f"            <label><input type='radio' name='result_{i}' value='partial'> ⚠️ Partiel (texte manquant)</label>")
            html.append(f"        </div>")
            html.append(f"        <textarea placeholder='Commentaires (ce qui manque, ce qui est incorrect, etc.)' name='comments_{i}'></textarea>")
            html.append(f"    </div>")
        
        html.append("    <div style='text-align: center; margin: 40px 0;'>")
        html.append("        <button onclick='exportResults()'>💾 Exporter les résultats</button>")
        html.append("    </div>")
        
        html.append("    <script>")
        html.append("        function exportResults() {")
        html.append("            const results = [];")
        html.append(f"            for (let i = 1; i <= {len(sample)}; i++) {{")
        html.append("                const result = document.querySelector(`input[name='result_${i}']:checked`);")
        html.append("                const comments = document.querySelector(`textarea[name='comments_${i}']`).value;")
        html.append("                results.push({")
        html.append("                    article: i,")
        html.append("                    result: result ? result.value : 'non_renseigne',")
        html.append("                    comments: comments")
        html.append("                });")
        html.append("            }")
        html.append("            const dataStr = JSON.stringify(results, null, 2);")
        html.append("            const blob = new Blob([dataStr], {type: 'application/json'});")
        html.append("            const url = URL.createObjectURL(blob);")
        html.append("            const a = document.createElement('a');")
        html.append("            a.href = url;")
        html.append("            a.download = 'audit_results.json';")
        html.append("            a.click();")
        html.append("        }")
        html.append("    </script>")
        html.append("</body>")
        html.append("</html>")
        
        return "\n".join(html)
    
    def run_audit(self):
        """Lance l'audit."""
        print("🔍 Démarrage de l'audit du parsing...")
        print("=" * 80)
        
        # Charger les articles
        articles = self.load_articles()
        if not articles:
            print("❌ Aucun article trouvé")
            return
        
        print(f"📊 Total d'articles parsés : {len(articles)}")
        
        # Échantillonner
        sample = self.sample_articles(articles)
        print(f"🎲 Échantillon sélectionné : {len(sample)} articles")
        
        # Générer le rapport texte
        report = self.generate_audit_report(sample)
        report_file = self.save_report(report)
        
        # Générer le rapport HTML
        html_report = self.generate_html_report(sample)
        html_file = self.data_dir / "audit_parsing_report.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_report)
        
        print(f"✅ Rapport HTML généré : {html_file}")
        print("\n" + "=" * 80)
        print("📋 PROCHAINES ÉTAPES :")
        print(f"1. Ouvrez le rapport HTML : {html_file}")
        print(f"2. Ou consultez le rapport texte : {report_file}")
        print("3. Pour chaque article, comparez le texte extrait avec l'article original")
        print("4. Notez les erreurs de parsing")
        print("5. Utilisez ces informations pour améliorer le script parse_articles.py")
        print("=" * 80)
        
        # Demander si on veut ouvrir le rapport HTML
        try:
            response = input("\nVoulez-vous ouvrir le rapport HTML maintenant ? (o/n): ")
            if response.lower() in ['o', 'oui', 'y', 'yes']:
                webbrowser.open(f"file://{html_file.absolute()}")
        except:
            pass


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Audite la qualité du parsing des articles')
    parser.add_argument('--sample-size', type=int, default=20,
                       help='Taille de l\'échantillon à auditer (défaut: 20)')
    
    args = parser.parse_args()
    
    auditor = ParsingAuditor(sample_size=args.sample_size)
    auditor.run_audit()


if __name__ == "__main__":
    main()

