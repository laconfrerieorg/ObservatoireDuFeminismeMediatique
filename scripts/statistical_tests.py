#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de tests statistiques pour l'observatoire des médias.
Calcule les intervalles de confiance, tests de significativité, et métriques de fiabilité.
"""

import os
import sys
import csv
import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict
from scipy import stats
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))


class StatisticalAnalyzer:
    """Effectue des analyses statistiques sur les scores."""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / "data"
        self.scores_file = self.data_dir / "scores.csv"
        self.output_file = self.data_dir / "statistical_analysis.json"
    
    def load_scores(self) -> List[Dict]:
        """Charge les scores depuis le fichier CSV."""
        if not self.scores_file.exists():
            print(f"❌ Fichier introuvable: {self.scores_file}")
            return []
        
        scores = []
        with open(self.scores_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    row['pct_militantisme'] = float(row.get('pct_militantisme', 0))
                    row['score_feministe'] = int(row.get('score_feministe', 0))
                    row['text_length'] = int(row.get('text_length', 0))
                    scores.append(row)
                except (ValueError, KeyError) as e:
                    print(f"⚠️  Erreur lors du chargement d'une ligne: {e}")
                    continue
        
        return scores
    
    def calculate_confidence_interval(self, data: List[float], confidence: float = 0.95) -> Tuple[float, float, float]:
        """
        Calcule l'intervalle de confiance pour une moyenne.
        
        Returns:
            (moyenne, borne_inférieure, borne_supérieure)
        """
        if len(data) < 2:
            return (np.mean(data), np.mean(data), np.mean(data))
        
        data_array = np.array(data)
        n = len(data_array)
        mean = np.mean(data_array)
        std = np.std(data_array, ddof=1)  # ddof=1 pour échantillon (n-1)
        
        # Calcul du t-score pour l'intervalle de confiance
        alpha = 1 - confidence
        t_score = stats.t.ppf(1 - alpha/2, df=n-1)
        
        # Erreur standard
        se = std / np.sqrt(n)
        
        # Intervalle de confiance
        ci_lower = mean - t_score * se
        ci_upper = mean + t_score * se
        
        return (mean, ci_lower, ci_upper)
    
    def test_normality(self, data: List[float]) -> Dict:
        """Teste si les données suivent une distribution normale."""
        if len(data) < 3:
            return {'is_normal': False, 'p_value': 0, 'test': 'insufficient_data'}
        
        data_array = np.array(data)
        
        # Test de Shapiro-Wilk (pour n < 5000)
        if len(data_array) < 5000:
            stat, p_value = stats.shapiro(data_array)
            test_name = 'shapiro-wilk'
        else:
            # Test de Kolmogorov-Smirnov pour grands échantillons
            stat, p_value = stats.kstest(data_array, 'norm')
            test_name = 'kolmogorov-smirnov'
        
        is_normal = p_value > 0.05
        
        return {
            'is_normal': is_normal,
            'p_value': float(p_value),
            'statistic': float(stat),
            'test': test_name
        }
    
    def compare_two_medias(self, media1_scores: List[float], media2_scores: List[float], 
                          media1_name: str, media2_name: str) -> Dict:
        """
        Compare deux médias avec tests statistiques appropriés.
        """
        media1_array = np.array(media1_scores)
        media2_array = np.array(media2_scores)
        
        # Statistiques descriptives
        mean1 = np.mean(media1_array)
        mean2 = np.mean(media2_array)
        diff = mean1 - mean2
        
        # Intervalles de confiance
        ci1 = self.calculate_confidence_interval(media1_scores)
        ci2 = self.calculate_confidence_interval(media2_scores)
        
        # Tests de normalité
        norm1 = self.test_normality(media1_scores)
        norm2 = self.test_normality(media2_scores)
        
        # Choisir le test approprié
        both_normal = norm1['is_normal'] and norm2['is_normal']
        
        if both_normal:
            # Test t de Student (paramétrique)
            t_stat, p_value = stats.ttest_ind(media1_array, media2_array)
            test_name = 't-test'
            test_statistic = float(t_stat)
        else:
            # Test de Mann-Whitney (non-paramétrique)
            u_stat, p_value = stats.mannwhitneyu(media1_array, media2_array, alternative='two-sided')
            test_name = 'mann-whitney'
            test_statistic = float(u_stat)
        
        # Taille d'effet (Cohen's d)
        pooled_std = np.sqrt((np.var(media1_array, ddof=1) + np.var(media2_array, ddof=1)) / 2)
        if pooled_std > 0:
            cohens_d = diff / pooled_std
        else:
            cohens_d = 0
        
        # Interprétation de la taille d'effet
        if abs(cohens_d) < 0.2:
            effect_size = 'négligeable'
        elif abs(cohens_d) < 0.5:
            effect_size = 'faible'
        elif abs(cohens_d) < 0.8:
            effect_size = 'modéré'
        else:
            effect_size = 'fort'
        
        # Interprétation de la significativité
        is_significant = p_value < 0.05
        
        return {
            'media1': media1_name,
            'media2': media2_name,
            'mean1': float(mean1),
            'mean2': float(mean2),
            'difference': float(diff),
            'ci1': {'mean': float(ci1[0]), 'lower': float(ci1[1]), 'upper': float(ci1[2])},
            'ci2': {'mean': float(ci2[0]), 'lower': float(ci2[1]), 'upper': float(ci2[2])},
            'test': test_name,
            'test_statistic': test_statistic,
            'p_value': float(p_value),
            'is_significant': is_significant,
            'cohens_d': float(cohens_d),
            'effect_size': effect_size,
            'normality': {
                'media1': norm1,
                'media2': norm2
            }
        }
    
    def analyze_by_media(self, scores: List[Dict]) -> Dict:
        """Analyse les scores par média."""
        scores_by_media = defaultdict(list)
        
        for score in scores:
            domain = score.get('domain', 'unknown')
            scores_by_media[domain].append(score['pct_militantisme'])
        
        results = {}
        
        for media, media_scores in scores_by_media.items():
            if len(media_scores) < 2:
                continue
            
            # Statistiques descriptives
            mean = np.mean(media_scores)
            median = np.median(media_scores)
            std = np.std(media_scores, ddof=1)
            n = len(media_scores)
            
            # Intervalle de confiance
            ci = self.calculate_confidence_interval(media_scores)
            
            # Test de normalité
            normality = self.test_normality(media_scores)
            
            results[media] = {
                'n': n,
                'mean': float(mean),
                'median': float(median),
                'std': float(std),
                'ci': {
                    'mean': float(ci[0]),
                    'lower': float(ci[1]),
                    'upper': float(ci[2])
                },
                'normality': normality
            }
        
        return results
    
    def compare_all_medias(self, scores: List[Dict]) -> List[Dict]:
        """Compare tous les médias deux à deux."""
        scores_by_media = defaultdict(list)
        
        for score in scores:
            domain = score.get('domain', 'unknown')
            scores_by_media[domain].append(score['pct_militantisme'])
        
        comparisons = []
        media_list = list(scores_by_media.keys())
        
        # Comparer chaque paire de médias
        for i, media1 in enumerate(media_list):
            for media2 in media_list[i+1:]:
                media1_scores = scores_by_media[media1]
                media2_scores = scores_by_media[media2]
                
                # Nécessite au moins 2 scores par média
                if len(media1_scores) >= 2 and len(media2_scores) >= 2:
                    comparison = self.compare_two_medias(
                        media1_scores, media2_scores, media1, media2
                    )
                    comparisons.append(comparison)
        
        return comparisons
    
    def calculate_correlation(self, scores: List[Dict]) -> Dict:
        """Calcule les corrélations entre variables."""
        text_lengths = [s['text_length'] for s in scores]
        pct_militantismes = [s['pct_militantisme'] for s in scores]
        scores_feministes = [s['score_feministe'] for s in scores]
        
        correlations = {}
        
        # Corrélation longueur vs score militant
        if len(text_lengths) > 2:
            corr_length_score, p_length = stats.pearsonr(text_lengths, pct_militantismes)
            correlations['length_vs_militantism'] = {
                'correlation': float(corr_length_score),
                'p_value': float(p_length),
                'is_significant': p_length < 0.05
            }
        
        # Corrélation score féministe vs pourcentage militantisme
        if len(scores_feministes) > 2:
            corr_score_pct, p_score = stats.pearsonr(scores_feministes, pct_militantismes)
            correlations['score_vs_percentage'] = {
                'correlation': float(corr_score_pct),
                'p_value': float(p_score),
                'is_significant': p_score < 0.05
            }
        
        return correlations
    
    def run_full_analysis(self):
        """Lance l'analyse statistique complète."""
        print("📊 Analyse statistique des scores")
        print("=" * 80)
        
        scores = self.load_scores()
        
        if not scores:
            print("❌ Aucun score trouvé")
            return
        
        print(f"📈 {len(scores)} articles analysés")
        
        # Analyse par média
        print("\n🔍 Analyse par média...")
        by_media = self.analyze_by_media(scores)
        
        print("\n📊 Statistiques par média:")
        print("-" * 80)
        for media, stats in sorted(by_media.items(), key=lambda x: x[1]['mean'], reverse=True):
            print(f"\n{media}:")
            print(f"  N = {stats['n']}")
            print(f"  Moyenne = {stats['mean']:.2f}%")
            print(f"  Médiane = {stats['median']:.2f}%")
            print(f"  Écart-type = {stats['std']:.2f}")
            print(f"  IC 95% = [{stats['ci']['lower']:.2f}, {stats['ci']['upper']:.2f}]")
            print(f"  Distribution normale: {stats['normality']['is_normal']} (p={stats['normality']['p_value']:.4f})")
        
        # Comparaisons deux à deux
        print("\n🔬 Comparaisons entre médias:")
        print("-" * 80)
        comparisons = self.compare_all_medias(scores)
        
        for comp in comparisons[:10]:  # Afficher les 10 premières
            print(f"\n{comp['media1']} vs {comp['media2']}:")
            print(f"  Différence = {comp['difference']:.2f} points")
            print(f"  Test = {comp['test']} (statistique = {comp['test_statistic']:.3f})")
            print(f"  p-value = {comp['p_value']:.4f}")
            print(f"  Significatif: {'✅ Oui' if comp['is_significant'] else '❌ Non'}")
            print(f"  Taille d'effet (Cohen's d) = {comp['cohens_d']:.3f} ({comp['effect_size']})")
        
        # Corrélations
        print("\n🔗 Corrélations:")
        print("-" * 80)
        correlations = self.calculate_correlation(scores)
        
        for name, corr in correlations.items():
            print(f"\n{name}:")
            print(f"  Corrélation = {corr['correlation']:.3f}")
            print(f"  p-value = {corr['p_value']:.4f}")
            print(f"  Significatif: {'✅ Oui' if corr['is_significant'] else '❌ Non'}")
        
        # Sauvegarder les résultats
        results = {
            'analysis_date': datetime.now().isoformat(),
            'total_articles': len(scores),
            'by_media': by_media,
            'comparisons': comparisons,
            'correlations': correlations
        }
        
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Résultats sauvegardés dans {self.output_file}")
        print("=" * 80)


def main():
    analyzer = StatisticalAnalyzer()
    analyzer.run_full_analysis()


if __name__ == "__main__":
    main()

