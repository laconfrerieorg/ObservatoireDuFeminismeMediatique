#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de génération des statistiques agrégées.
Calcule les stats par média, par période, etc.
"""

import os
import sys
import csv
import json
import statistics
import math
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict, List

# Augmenter la limite de taille de champ CSV (défaut: 131072)
# Utiliser 50MB au lieu de sys.maxsize pour éviter l'erreur sur Windows
csv.field_size_limit(50 * 1024 * 1024)  # 50MB

sys.path.insert(0, str(Path(__file__).parent.parent))


class StatsBuilder:
    """Génère les statistiques agrégées à partir des scores."""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / "data"
        self.scores_file = self.data_dir / "scores.csv"
        self.stats_file = self.data_dir / "stats_daily.json"
        self.articles_file = self.data_dir / "articles_clean.csv"
    
    def _load_scores(self) -> List[Dict]:
        """Charge tous les scores."""
        if not self.scores_file.exists():
            return []
        
        scores = []
        with open(self.scores_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convertir les valeurs numériques
                row['score_feministe'] = int(row.get('score_feministe', 0))
                row['score_balance'] = int(row.get('score_balance', 0))
                row['indice_militant'] = int(row.get('indice_militant', 0))
                row['text_length'] = int(row.get('text_length', 0))
                row['densite_militant'] = float(row.get('densite_militant', 0))
                # Convertir pct_militantisme (peut ne pas exister dans les anciens scores)
                pct_militant = row.get('pct_militantisme', '')
                if pct_militant == '':
                    # Si manquant, mettre à 0 (sera recalculé lors de la prochaine analyse)
                    row['pct_militantisme'] = 0.0
                else:
                    try:
                        row['pct_militantisme'] = float(pct_militant)
                    except (ValueError, TypeError):
                        row['pct_militantisme'] = 0.0
                scores.append(row)
        
        return scores
    
    def _load_articles(self) -> Dict[str, Dict]:
        """Charge les articles pour récupérer les titres."""
        articles = {}
        if self.articles_file.exists():
            with open(self.articles_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    articles[row['url']] = row
        return articles
    
    def _extract_year(self, date_str: str) -> int:
        """Extrait l'année d'une date."""
        if not date_str:
            return None
        
        try:
            # Essayer de parser la date
            from dateutil import parser as date_parser
            dt = date_parser.parse(date_str, fuzzy=True)
            year = dt.year
            # Filtrer les années futures (après 2025) et trop anciennes (avant 2000)
            if year < 2000 or year > 2025:
                return None
            return year
        except:
            return None
    
    def build_stats(self):
        """Construit les statistiques agrégées."""
        print("📊 Génération des statistiques...")
        
        scores = self._load_scores()
        articles = self._load_articles()
        
        if not scores:
            print("❌ Aucun score trouvé")
            return
        
        # Stats par média
        stats_by_domain = defaultdict(lambda: {
            'n_articles': 0,
            'scores_feministes': [],
            'indices_militants': [],
            'densites_militants': []
        })
        
        # Stats par période
        stats_by_period = defaultdict(lambda: {
            'n_articles': 0,
            'indices_militants': [],
            'pct_militantismes': []
        })
        
        # Top articles les plus militants
        top_militant = []
        
        for score in scores:
            domain = score.get('domain', 'unknown')
            date_pub = score.get('date_pub', '')
            
            # Filtrer franceculture.fr (média exclu)
            if domain == 'franceculture.fr' or 'franceculture.fr' in domain:
                continue
            
            # Filtrer les articles publiés avant 2000 ou après 2025
            year = self._extract_year(date_pub)
            if year and (year < 2000 or year > 2025):
                continue
            
            # Stats par domaine
            stats_by_domain[domain]['n_articles'] += 1
            stats_by_domain[domain]['scores_feministes'].append(score['score_feministe'])
            stats_by_domain[domain]['indices_militants'].append(score['indice_militant'])
            stats_by_domain[domain]['densites_militants'].append(score['densite_militant'])
            # Nouveau: pourcentage de militantisme
            pct_militant = score.get('pct_militantisme', 0.0)
            # S'assurer que c'est un float
            if isinstance(pct_militant, str):
                try:
                    pct_militant = float(pct_militant)
                except (ValueError, TypeError):
                    pct_militant = 0.0
            elif not isinstance(pct_militant, (int, float)):
                pct_militant = 0.0
            else:
                pct_militant = float(pct_militant)
            
            if 'pct_militantisme' not in stats_by_domain[domain]:
                stats_by_domain[domain]['pct_militantisme'] = []
            stats_by_domain[domain]['pct_militantisme'].append(pct_militant)
            
            # Stats par période (par année)
            year = self._extract_year(date_pub)
            if year:
                period_key = str(year)
                stats_by_period[period_key]['n_articles'] += 1
                stats_by_period[period_key]['indices_militants'].append(score['indice_militant'])
                # Ajouter le pourcentage de militantisme
                pct_militant = score.get('pct_militantisme', 0.0)
                if isinstance(pct_militant, str):
                    try:
                        pct_militant = float(pct_militant)
                    except:
                        pct_militant = 0.0
                stats_by_period[period_key]['pct_militantismes'].append(float(pct_militant))
            
            # Top militant
            article_info = articles.get(score['url'], {})
            top_militant.append({
                'url': score['url'],
                'title': article_info.get('title', ''),
                'domain': domain,
                'date_pub': date_pub,
                'pct_militantisme': score.get('pct_militantisme', 0),
                'indice_militant': score['indice_militant'],
                'densite_militant': score['densite_militant'],
                'score_feministe': score['score_feministe']
            })
        
        # Calculer les moyennes normalisées par nombre d'articles
        medias_stats = []
        for domain, stats in stats_by_domain.items():
            n = stats['n_articles']
            # Calculer le nombre MOYEN de mots-clés féministes par article (pour comparer équitablement)
            moyenne_mots_cles_feministes = sum(stats['scores_feministes']) / n if n > 0 else 0
            total_mots_cles_feministes = sum(stats['scores_feministes'])
            
            # Calculer médiane et écart-type pour les scores féministes
            scores_fem_list = stats['scores_feministes']
            mediane_score_feministe = statistics.median(scores_fem_list) if scores_fem_list else 0
            ecart_type_score_feministe = statistics.stdev(scores_fem_list) if len(scores_fem_list) > 1 else 0
            
            # Calculer médiane et écart-type pour le pourcentage de militantisme
            pct_militant_list = stats.get('pct_militantisme', [])
            if pct_militant_list:
                mediane_pct_militantisme = statistics.median(pct_militant_list)
                ecart_type_pct_militantisme = statistics.stdev(pct_militant_list) if len(pct_militant_list) > 1 else 0
                moyenne_pct_militantisme = statistics.mean(pct_militant_list)
            else:
                mediane_pct_militantisme = 0
                ecart_type_pct_militantisme = 0
                moyenne_pct_militantisme = 0
            
            # Calculer un facteur de confiance basé sur le nombre d'articles
            # Plus il y a d'articles, plus la moyenne est fiable statistiquement
            # Formule: facteur de confiance qui augmente avec le nombre d'articles
            # Utilise une fonction sigmoïde pour avoir une croissance rapide jusqu'à ~100 articles, puis ralentit
            # facteur_confiance = 1 - exp(-n_articles / 50) donne ~0.63 à 50 articles, ~0.86 à 100, ~0.98 à 200
            facteur_confiance = 1 - math.exp(-n / 50.0) if n > 0 else 0
            
            # Score ajusté qui combine le pourcentage de militantisme avec le facteur de confiance
            # Cela pénalise les médias avec peu d'articles (moins de confiance statistique)
            score_ajuste = moyenne_pct_militantisme * facteur_confiance
            
            medias_stats.append({
                'domain': domain,
                'n_articles': n,
                'moyenne_mots_cles_feministes': round(moyenne_mots_cles_feministes, 2),  # Moyenne par article (métrique principale)
                'mediane_mots_cles_feministes': round(mediane_score_feministe, 2),
                'ecart_type_mots_cles_feministes': round(ecart_type_score_feministe, 2),
                'total_mots_cles_feministes': total_mots_cles_feministes,  # Total pour référence
                'score_feministe_moyen': round(
                    sum(stats['scores_feministes']) / n if n > 0 else 0, 2
                ),
                'pct_militantisme_moyen': round(moyenne_pct_militantisme, 1),
                'pct_militantisme_mediane': round(mediane_pct_militantisme, 1),
                'pct_militantisme_ecart_type': round(ecart_type_pct_militantisme, 1),
                'facteur_confiance': round(facteur_confiance, 3),  # Facteur de confiance basé sur n_articles
                'score_ajuste': round(score_ajuste, 2),  # Score ajusté pour le classement
                'indice_militant_moyen': round(
                    sum(stats['indices_militants']) / n if n > 0 else 0, 2
                ),
                'densite_militant_moyenne': round(
                    sum(stats['densites_militants']) / n if n > 0 else 0, 3
                ),
                'indice_militant_max': max(stats['indices_militants']) if stats['indices_militants'] else 0,
                'indice_militant_min': min(stats['indices_militants']) if stats['indices_militants'] else 0
            })
        
        # Trier par score ajusté (décroissant)
        # Le score ajusté combine le pourcentage de militantisme avec un facteur de confiance
        # basé sur le nombre d'articles. Cela pénalise les médias avec peu d'articles
        # (moins de confiance statistique) et favorise ceux avec un échantillon plus représentatif.
        medias_stats.sort(key=lambda x: x['score_ajuste'], reverse=True)
        
        # Stats par période (par année)
        period_stats = []
        for period, stats in sorted(stats_by_period.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 0):
            n = stats['n_articles']
            pct_militant_list = stats.get('pct_militantismes', [])
            # Calculer aussi la moyenne de mots-clés féministes par période
            moyenne_mots_cles = sum(stats['indices_militants']) / n if n > 0 else 0
            period_stats.append({
                'period': period,
                'year': int(period) if period.isdigit() else 0,
                'n_articles': n,
                'pct_militantisme_moyen': round(
                    sum(float(x) for x in pct_militant_list) / n if n > 0 and pct_militant_list else 0, 1
                ),
                'indice_militant_moyen': round(
                    sum(stats['indices_militants']) / n if n > 0 else 0, 2
                ),
                'moyenne_mots_cles_feministes': round(moyenne_mots_cles, 2)
            })
        
        # Top 10 articles avec le plus de mots-clés féministes (tri par score féministe)
        top_militant.sort(key=lambda x: x.get('score_feministe', 0), reverse=True)
        top_10 = top_militant[:10]
        
        # Tous les articles organisés par média
        all_articles_by_media = defaultdict(list)
        for article_info in top_militant:
            domain = article_info.get('domain', 'unknown')
            all_articles_by_media[domain].append({
                'url': article_info['url'],
                'title': article_info.get('title', ''),
                'date_pub': article_info.get('date_pub', ''),
                'score_feministe': article_info.get('score_feministe', 0),
                'pct_militantisme': article_info.get('pct_militantisme', 0),
                'indice_militant': article_info.get('indice_militant', 0)
            })
        
        # Trier les articles par score décroissant dans chaque média
        for domain in all_articles_by_media:
            all_articles_by_media[domain].sort(key=lambda x: x.get('score_feministe', 0), reverse=True)
        
        # Convertir en liste pour JSON
        all_articles_list = []
        for domain, articles_list in sorted(all_articles_by_media.items()):
            all_articles_list.append({
                'domain': domain,
                'n_articles': len(articles_list),
                'articles': articles_list
            })
        
        # Construire le JSON final
        stats_data = {
            'generated_at': datetime.now().isoformat(),
            'total_articles': len(scores),
            'medias': medias_stats,
            'by_period': period_stats,
            'top_militant_articles': top_10,
            'all_articles_by_media': all_articles_list,
            'summary': {
                'total_mots_cles_feministes_global': sum(s['score_feministe'] for s in scores),  # Total global de mots-clés féministes
                'indice_militant_moyen_global': round(
                    sum(s['indice_militant'] for s in scores) / len(scores), 2
                ),
                'n_medias': len(medias_stats)
            }
        }
        
        # Sauvegarder
        with open(self.stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Statistiques générées: {self.stats_file}")
        print(f"\n📈 Résumé:")
        print(f"   Total articles: {stats_data['total_articles']}")
        print(f"   Total mots-clés féministes: {stats_data['summary']['total_mots_cles_feministes_global']}")
        print(f"\n🏆 Top 3 médias par moyenne de mots-clés féministes par article:")
        for i, media in enumerate(medias_stats[:3], 1):
            print(f"   {i}. {media['domain']}: {media['moyenne_mots_cles_feministes']} mots-clés/article ({media['n_articles']} articles)")


def main():
    builder = StatsBuilder()
    builder.build_stats()


if __name__ == "__main__":
    main()

