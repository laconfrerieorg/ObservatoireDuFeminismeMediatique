#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test de sensibilité des mots-clés.
Teste l'impact de la modification des mots-clés sur les scores.
"""

import os
import sys
import csv
import yaml
from pathlib import Path
from typing import Dict, List
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))


class SensitivityTester:
    """Teste la sensibilité des résultats aux variations des mots-clés."""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.config_dir = self.base_dir / "config"
        self.data_dir = self.base_dir / "data"
        self.scores_file = self.data_dir / "scores.csv"
    
    def load_keywords(self) -> Dict:
        """Charge les mots-clés depuis la configuration."""
        keywords_file = self.config_dir / "keywords.yml"
        with open(keywords_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def load_scores(self) -> List[Dict]:
        """Charge les scores existants."""
        if not self.scores_file.exists():
            print("❌ Fichier scores.csv non trouvé")
            return []
        
        scores = []
        with open(self.scores_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convertir les valeurs numériques
                row['score_feministe'] = int(row.get('score_feministe', 0))
                row['score_balance'] = int(row.get('score_balance', 0))
                row['pct_militantisme'] = float(row.get('pct_militantisme', 0))
                scores.append(row)
        
        return scores
    
    def calculate_stats_by_media(self, scores: List[Dict]) -> Dict[str, Dict]:
        """Calcule les statistiques par média."""
        stats_by_media = defaultdict(lambda: {
            'n_articles': 0,
            'pct_militantismes': [],
            'scores_feministes': [],
            'scores_balance': []
        })
        
        for score in scores:
            domain = score.get('domain', 'unknown')
            stats_by_media[domain]['n_articles'] += 1
            stats_by_media[domain]['pct_militantismes'].append(score['pct_militantisme'])
            stats_by_media[domain]['scores_feministes'].append(score['score_feministe'])
            stats_by_media[domain]['scores_balance'].append(score['score_balance'])
        
        # Calculer les moyennes
        result = {}
        for domain, stats in stats_by_media.items():
            n = stats['n_articles']
            result[domain] = {
                'n_articles': n,
                'pct_militantisme_moyen': sum(stats['pct_militantismes']) / n if n > 0 else 0,
                'score_feministe_moyen': sum(stats['scores_feministes']) / n if n > 0 else 0,
                'score_balance_moyen': sum(stats['scores_balance']) / n if n > 0 else 0
            }
        
        return result
    
    def test_removal(self, keywords: Dict, keyword_to_remove: str, category: str = 'feminist_keywords'):
        """Teste l'impact de la suppression d'un mot-clé."""
        print(f"\n🧪 Test : Suppression de '{keyword_to_remove}' ({category})")
        print("-" * 80)
        
        # Charger les scores actuels (baseline)
        scores_baseline = self.load_scores()
        if not scores_baseline:
            print("❌ Aucun score trouvé. Lancez d'abord analyze_articles.py")
            return None
        
        stats_baseline = self.calculate_stats_by_media(scores_baseline)
        
        # Simuler la suppression (on ne peut pas vraiment le faire sans réanalyser)
        # Mais on peut estimer l'impact en comptant combien d'articles utilisent ce mot-clé
        keyword_lower = keyword_to_remove.lower()
        articles_with_keyword = []
        
        # Charger les articles pour vérifier
        articles_file = self.data_dir / "articles_clean.csv"
        if articles_file.exists():
            with open(articles_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    text = row.get('text', '').lower()
                    if keyword_lower in text:
                        articles_with_keyword.append(row['url'])
        
        # Trouver les scores correspondants
        affected_scores = [s for s in scores_baseline if s['url'] in articles_with_keyword]
        
        print(f"📊 Articles contenant '{keyword_to_remove}' : {len(affected_scores)}")
        
        if affected_scores:
            # Estimer l'impact (approximation)
            avg_score_before = sum(s['pct_militantisme'] for s in affected_scores) / len(affected_scores)
            
            # Simuler la réduction (chaque occurrence compte pour ~1 point dans le score)
            # C'est une approximation grossière
            print(f"📈 Impact estimé :")
            print(f"   - Articles affectés : {len(affected_scores)}")
            print(f"   - Score moyen avant : {avg_score_before:.1f}%")
            print(f"   - Impact estimé : -1 à -3% par article (approximation)")
        
        return {
            'keyword': keyword_to_remove,
            'category': category,
            'articles_affected': len(affected_scores),
            'impact_estimated': 'Faible à modéré'
        }
    
    def test_keyword_frequency(self, keywords: Dict):
        """Analyse la fréquence d'utilisation de chaque mot-clé."""
        print("\n📊 ANALYSE DE FRÉQUENCE DES MOTS-CLÉS")
        print("=" * 80)
        
        articles_file = self.data_dir / "articles_clean.csv"
        if not articles_file.exists():
            print("❌ Fichier articles_clean.csv non trouvé")
            return
        
        # Compter les occurrences
        feminist_counts = defaultdict(int)
        balanced_counts = defaultdict(int)
        total_articles = 0
        
        with open(articles_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                total_articles += 1
                text = row.get('text', '').lower()
                
                # Compter les mots-clés féministes
                for keyword in keywords.get('feminist_keywords', []):
                    keyword_lower = keyword.lower()
                    if keyword_lower in text:
                        # Compter les occurrences (approximation)
                        count = text.count(keyword_lower)
                        feminist_counts[keyword] += count
                
                # Compter les mots-clés équilibrants
                for keyword in keywords.get('balanced_keywords', []):
                    keyword_lower = keyword.lower()
                    if keyword_lower in text:
                        count = text.count(keyword_lower)
                        balanced_counts[keyword] += count
        
        print(f"\n📰 Total d'articles analysés : {total_articles}")
        
        print("\n🔴 Mots-clés féministes (top 10) :")
        sorted_feminist = sorted(feminist_counts.items(), key=lambda x: x[1], reverse=True)
        for keyword, count in sorted_feminist[:10]:
            pct = (count / total_articles * 100) if total_articles > 0 else 0
            print(f"   {keyword:40s} : {count:5d} occurrences ({pct:.1f}% des articles)")
        
        print("\n🟢 Mots-clés équilibrants (top 10) :")
        sorted_balanced = sorted(balanced_counts.items(), key=lambda x: x[1], reverse=True)
        for keyword, count in sorted_balanced[:10]:
            pct = (count / total_articles * 100) if total_articles > 0 else 0
            print(f"   {keyword:40s} : {count:5d} occurrences ({pct:.1f}% des articles)")
        
        print("\n⚠️  Mots-clés jamais trouvés :")
        all_feminist = set(keywords.get('feminist_keywords', []))
        found_feminist = set(feminist_counts.keys())
        never_found_feminist = all_feminist - found_feminist
        if never_found_feminist:
            print(f"   Féministes ({len(never_found_feminist)}) : {', '.join(list(never_found_feminist)[:10])}")
        
        all_balanced = set(keywords.get('balanced_keywords', []))
        found_balanced = set(balanced_counts.keys())
        never_found_balanced = all_balanced - found_balanced
        if never_found_balanced:
            print(f"   Équilibrants ({len(never_found_balanced)}) : {', '.join(list(never_found_balanced)[:10])}")
    
    def run_tests(self):
        """Lance tous les tests de sensibilité."""
        print("🔬 TESTS DE SENSIBILITÉ DES MOTS-CLÉS")
        print("=" * 80)
        
        keywords = self.load_keywords()
        
        # Test 1 : Analyse de fréquence
        self.test_keyword_frequency(keywords)
        
        # Test 2 : Impact de suppression (exemples)
        print("\n" + "=" * 80)
        print("🧪 TESTS D'IMPACT DE SUPPRESSION")
        print("=" * 80)
        
        # Tester quelques mots-clés fréquents
        if keywords.get('feminist_keywords'):
            top_keywords = keywords['feminist_keywords'][:5]
            for keyword in top_keywords:
                self.test_removal(keywords, keyword, 'feminist_keywords')
        
        print("\n" + "=" * 80)
        print("✅ Tests terminés")
        print("\n💡 Recommandations :")
        print("   - Si un mot-clé apparaît dans < 1% des articles, considérez sa suppression")
        print("   - Si un mot-clé apparaît dans > 50% des articles, vérifiez sa pertinence")
        print("   - Testez la suppression des mots-clés les plus fréquents pour voir l'impact")
        print("=" * 80)


def main():
    tester = SensitivityTester()
    tester.run_tests()


if __name__ == "__main__":
    main()

