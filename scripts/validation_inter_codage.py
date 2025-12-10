#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de validation inter-codage pour mesurer la fiabilité du système.
Permet d'annoter manuellement un échantillon d'articles et de comparer avec les scores automatiques.
"""

import os
import sys
import csv
import json
import random
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict
from datetime import datetime

try:
    from sklearn.metrics import cohen_kappa_score, accuracy_score, precision_score, recall_score, f1_score
    from scipy.stats import pearsonr
except ImportError:
    print("⚠️  scikit-learn et scipy requis pour ce script")
    print("   Installez avec: pip install scikit-learn scipy")
    sys.exit(1)

sys.path.insert(0, str(Path(__file__).parent.parent))


class InterCoderValidator:
    """Valide la fiabilité du système par validation inter-codage."""
    
    def __init__(self, sample_size: int = 100):
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / "data"
        self.articles_file = self.data_dir / "articles_clean.csv"
        self.scores_file = self.data_dir / "scores.csv"
        self.annotations_file = self.data_dir / "manual_annotations.csv"
        self.results_file = self.data_dir / "validation_results.json"
        self.sample_size = sample_size
    
    def load_articles(self) -> List[Dict]:
        """Charge tous les articles."""
        if not self.articles_file.exists():
            print(f"❌ Fichier introuvable: {self.articles_file}")
            return []
        
        articles = []
        with open(self.articles_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                articles.append(row)
        
        return articles
    
    def load_scores(self) -> Dict[str, Dict]:
        """Charge les scores automatiques."""
        if not self.scores_file.exists():
            print(f"❌ Fichier introuvable: {self.scores_file}")
            return {}
        
        scores = {}
        with open(self.scores_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                scores[row['url']] = {
                    'pct_militantisme': float(row.get('pct_militantisme', 0)),
                    'score_feministe': int(row.get('score_feministe', 0))
                }
        
        return scores
    
    def sample_articles(self, articles: List[Dict], n: Optional[int] = None) -> List[Dict]:
        """Échantillonne aléatoirement des articles."""
        if n is None:
            n = self.sample_size
        
        if len(articles) <= n:
            return articles
        
        return random.sample(articles, n)
    
    def create_annotation_template(self, sample: List[Dict], scores: Dict[str, Dict]):
        """Crée un fichier CSV pour l'annotation manuelle."""
        print(f"📝 Création du fichier d'annotation pour {len(sample)} articles...")
        
        fieldnames = [
            'url', 'title', 'text_preview', 'auto_score', 'auto_pct',
            'manual_score', 'manual_category', 'notes'
        ]
        
        with open(self.annotations_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for article in sample:
                url = article['url']
                title = article.get('title', '')[:100]
                text = article.get('text', '')[:500]  # Aperçu de 500 caractères
                
                auto_score = scores.get(url, {})
                auto_pct = auto_score.get('pct_militantisme', 0)
                auto_score_val = auto_score.get('score_feministe', 0)
                
                writer.writerow({
                    'url': url,
                    'title': title,
                    'text_preview': text,
                    'auto_score': auto_score_val,
                    'auto_pct': auto_pct,
                    'manual_score': '',  # À remplir manuellement
                    'manual_category': '',  # À remplir manuellement
                    'notes': ''  # Notes optionnelles
                })
        
        print(f"✅ Fichier créé: {self.annotations_file}")
        print("\n📋 Instructions pour l'annotation:")
        print("   1. Ouvrez le fichier CSV dans Excel ou un éditeur de texte")
        print("   2. Pour chaque article, remplissez:")
        print("      - manual_score: Score de militantisme (0-100)")
        print("      - manual_category: 'militant', 'modéré', 'neutre', 'critique'")
        print("      - notes: Notes optionnelles")
        print("   3. Sauvegardez le fichier")
        print("   4. Relancez ce script avec --analyze pour calculer les métriques")
    
    def load_annotations(self) -> List[Dict]:
        """Charge les annotations manuelles."""
        if not self.annotations_file.exists():
            print(f"❌ Fichier d'annotation introuvable: {self.annotations_file}")
            print("   Créez-le d'abord avec --create-template")
            return []
        
        annotations = []
        with open(self.annotations_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Ignorer les lignes non annotées
                if row.get('manual_score') and row['manual_score'].strip():
                    try:
                        row['manual_score'] = float(row['manual_score'])
                        annotations.append(row)
                    except ValueError:
                        continue
        
        return annotations
    
    def calculate_metrics(self, annotations: List[Dict]) -> Dict:
        """Calcule les métriques de fiabilité."""
        if len(annotations) < 2:
            print("❌ Pas assez d'annotations (minimum 2 requis)")
            return {}
        
        auto_scores = [float(a['auto_pct']) for a in annotations]
        manual_scores = [float(a['manual_score']) for a in annotations]
        
        # Corrélation de Pearson
        correlation, p_corr = pearsonr(auto_scores, manual_scores)
        
        # Catégorisation pour Kappa
        # Convertir en catégories: 0-25 = faible, 25-50 = modéré, 50-75 = élevé, 75-100 = très élevé
        def categorize(score):
            if score < 25:
                return 0  # Faible
            elif score < 50:
                return 1  # Modéré
            elif score < 75:
                return 2  # Élevé
            else:
                return 3  # Très élevé
        
        auto_categories = [categorize(s) for s in auto_scores]
        manual_categories = [categorize(s) for s in manual_scores]
        
        # Coefficient Kappa de Cohen
        kappa = cohen_kappa_score(manual_categories, auto_categories)
        
        # Précision, Rappel, F1 (en considérant "militant" = score >= 30)
        auto_binary = [1 if s >= 30 else 0 for s in auto_scores]
        manual_binary = [1 if s >= 30 else 0 for s in manual_scores]
        
        accuracy = accuracy_score(manual_binary, auto_binary)
        precision = precision_score(manual_binary, auto_binary, zero_division=0)
        recall = recall_score(manual_binary, auto_binary, zero_division=0)
        f1 = f1_score(manual_binary, auto_binary, zero_division=0)
        
        # Erreur moyenne absolue (MAE)
        mae = sum(abs(a - m) for a, m in zip(auto_scores, manual_scores)) / len(annotations)
        
        # Erreur quadratique moyenne (RMSE)
        rmse = (sum((a - m) ** 2 for a, m in zip(auto_scores, manual_scores)) / len(annotations)) ** 0.5
        
        return {
            'n_annotations': len(annotations),
            'correlation': {
                'pearson_r': float(correlation),
                'p_value': float(p_corr),
                'is_significant': p_corr < 0.05
            },
            'kappa': {
                'value': float(kappa),
                'interpretation': self._interpret_kappa(kappa)
            },
            'binary_classification': {
                'accuracy': float(accuracy),
                'precision': float(precision),
                'recall': float(recall),
                'f1_score': float(f1)
            },
            'regression_metrics': {
                'mae': float(mae),
                'rmse': float(rmse)
            }
        }
    
    def _interpret_kappa(self, kappa: float) -> str:
        """Interprète le coefficient Kappa."""
        if kappa < 0:
            return "Accord pire que le hasard"
        elif kappa < 0.2:
            return "Accord faible"
        elif kappa < 0.4:
            return "Accord passable"
        elif kappa < 0.6:
            return "Accord modéré"
        elif kappa < 0.8:
            return "Accord bon"
        else:
            return "Accord excellent"
    
    def print_results(self, metrics: Dict):
        """Affiche les résultats de validation."""
        print("\n" + "=" * 80)
        print("📊 RÉSULTATS DE VALIDATION INTER-CODAGE")
        print("=" * 80)
        
        print(f"\n📈 Nombre d'articles annotés: {metrics['n_annotations']}")
        
        print("\n🔗 Corrélation:")
        corr = metrics['correlation']
        print(f"   Coefficient de Pearson (r) = {corr['pearson_r']:.3f}")
        print(f"   p-value = {corr['p_value']:.4f}")
        print(f"   Significatif: {'✅ Oui' if corr['is_significant'] else '❌ Non'}")
        
        print("\n📊 Coefficient Kappa de Cohen:")
        kappa = metrics['kappa']
        print(f"   Kappa = {kappa['value']:.3f}")
        print(f"   Interprétation: {kappa['interpretation']}")
        
        print("\n🎯 Classification binaire (militant vs non-militant):")
        binary = metrics['binary_classification']
        print(f"   Précision = {binary['precision']:.3f}")
        print(f"   Rappel = {binary['recall']:.3f}")
        print(f"   F1-Score = {binary['f1_score']:.3f}")
        print(f"   Exactitude = {binary['accuracy']:.3f}")
        
        print("\n📉 Métriques de régression:")
        reg = metrics['regression_metrics']
        print(f"   Erreur moyenne absolue (MAE) = {reg['mae']:.2f}")
        print(f"   Erreur quadratique moyenne (RMSE) = {reg['rmse']:.2f}")
        
        print("\n✅ Objectifs de qualité:")
        print(f"   Kappa > 0.7: {'✅ Atteint' if kappa['value'] > 0.7 else '❌ Non atteint'}")
        print(f"   F1 > 0.75: {'✅ Atteint' if binary['f1_score'] > 0.75 else '❌ Non atteint'}")
        print(f"   Corrélation > 0.8: {'✅ Atteint' if corr['pearson_r'] > 0.8 else '❌ Non atteint'}")
        
        print("=" * 80)
    
    def run_validation(self):
        """Lance la validation complète."""
        annotations = self.load_annotations()
        
        if not annotations:
            return
        
        metrics = self.calculate_metrics(annotations)
        
        if not metrics:
            return
        
        self.print_results(metrics)
        
        # Sauvegarder les résultats
        results = {
            'validation_date': datetime.now().isoformat(),
            'metrics': metrics
        }
        
        with open(self.results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Résultats sauvegardés dans {self.results_file}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Validation inter-codage')
    parser.add_argument('--create-template', action='store_true',
                       help='Crée un fichier CSV pour annotation manuelle')
    parser.add_argument('--analyze', action='store_true',
                       help='Analyse les annotations et calcule les métriques')
    parser.add_argument('--sample-size', type=int, default=100,
                       help='Taille de l\'échantillon (défaut: 100)')
    
    args = parser.parse_args()
    
    validator = InterCoderValidator(sample_size=args.sample_size)
    
    if args.create_template:
        articles = validator.load_articles()
        if not articles:
            return
        
        scores = validator.load_scores()
        sample = validator.sample_articles(articles)
        validator.create_annotation_template(sample, scores)
    
    elif args.analyze:
        validator.run_validation()
    
    else:
        print("Usage:")
        print("  Créer le template: python validation_inter_codage.py --create-template")
        print("  Analyser: python validation_inter_codage.py --analyze")


if __name__ == "__main__":
    main()

