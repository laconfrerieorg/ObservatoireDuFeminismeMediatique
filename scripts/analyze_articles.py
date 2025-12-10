#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script d'analyse et de scoring idéologique des articles.
Calcule les scores féministes, équilibrants et l'indice militant.
"""

import os
import sys
import csv
import yaml
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from collections import Counter

# Augmenter la limite de taille de champ CSV (défaut: 131072)
# Utiliser 50MB au lieu de sys.maxsize pour éviter l'erreur sur Windows
csv.field_size_limit(50 * 1024 * 1024)  # 50MB

sys.path.insert(0, str(Path(__file__).parent.parent))


class ArticleAnalyzer:
    """Analyse les articles et calcule les scores idéologiques."""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.config_dir = self.base_dir / "config"
        self.data_dir = self.base_dir / "data"
        
        self.keywords = self._load_config("keywords.yml")
        self.articles_file = self.data_dir / "articles_clean.csv"
        self.scores_file = self.data_dir / "scores.csv"
        
        # Préparer les patterns avec pondération
        self.feminist_patterns_weighted = self._prepare_weighted_patterns(
            self.keywords.get("feminist_keywords", {})
        )
        
        # Compatibilité avec l'ancien format (liste simple)
        if isinstance(self.keywords.get("feminist_keywords"), list):
            self.feminist_patterns = self._prepare_patterns(
                self.keywords.get("feminist_keywords", [])
            )
        else:
            self.feminist_patterns = []
    
    def _load_config(self, filename: str) -> Dict:
        """Charge un fichier de configuration YAML."""
        config_path = self.config_dir / filename
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _prepare_patterns(self, keywords: List[str]) -> List[re.Pattern]:
        """Prépare les patterns regex pour la recherche de mots-clés (ancien format)."""
        patterns = []
        for keyword in keywords:
            # Échapper les caractères spéciaux et créer un pattern insensible à la casse
            escaped = re.escape(keyword)
            pattern = re.compile(rf'\b{escaped}\b', re.IGNORECASE | re.UNICODE)
            patterns.append(pattern)
        return patterns
    
    def _prepare_weighted_patterns(self, keywords_config: Dict) -> List[Dict]:
        """Prépare les patterns regex avec leurs pondérations (nouveau format)."""
        patterns_weighted = []
        
        if isinstance(keywords_config, dict):
            # Nouveau format avec catégories et poids
            for category_name, category_data in keywords_config.items():
                if isinstance(category_data, dict) and 'keywords' in category_data:
                    weight = category_data.get('weight', 1)
                    keywords = category_data.get('keywords', [])
                    
                    for keyword in keywords:
                        escaped = re.escape(keyword)
                        pattern = re.compile(rf'\b{escaped}\b', re.IGNORECASE | re.UNICODE)
                        patterns_weighted.append({
                            'pattern': pattern,
                            'weight': weight,
                            'keyword': keyword,
                            'category': category_name
                        })
        elif isinstance(keywords_config, list):
            # Ancien format (liste simple) - poids par défaut = 1
            for keyword in keywords_config:
                escaped = re.escape(keyword)
                pattern = re.compile(rf'\b{escaped}\b', re.IGNORECASE | re.UNICODE)
                patterns_weighted.append({
                    'pattern': pattern,
                    'weight': 1,
                    'keyword': keyword,
                    'category': 'default'
                })
        
        return patterns_weighted
    
    def _count_matches(self, text: str, patterns: List[re.Pattern]) -> int:
        """Compte le nombre d'occurrences des patterns dans le texte (ancien format)."""
        count = 0
        for pattern in patterns:
            matches = pattern.findall(text)
            count += len(matches)
        return count
    
    def _count_weighted_matches(self, text: str, patterns_weighted: List[Dict]) -> int:
        """Compte le nombre d'occurrences pondérées des patterns dans le texte."""
        total_score = 0
        for item in patterns_weighted:
            pattern = item['pattern']
            weight = item['weight']
            matches = pattern.findall(text)
            total_score += len(matches) * weight
        return total_score
    
    def _calculate_density(self, score: int, text_length: int) -> float:
        """Calcule la densité d'un score par rapport à la longueur du texte."""
        if text_length == 0:
            return 0.0
        # Normaliser sur 1000 caractères
        normalized_length = text_length / 1000.0
        return score / normalized_length if normalized_length > 0 else 0.0
    
    def _is_article_date_invalid(self, date_str: str, min_year: int = 2000, max_year: int = 2025) -> bool:
        """Vérifie si un article a une date invalide (trop ancienne ou future)."""
        if not date_str:
            return False  # Si pas de date, on garde l'article
        
        try:
            from dateutil import parser as date_parser
            parsed_date = date_parser.parse(date_str, fuzzy=True)
            year = parsed_date.year
            return year < min_year or year > max_year
        except:
            return False  # Si erreur de parsing, on garde l'article
    
    def analyze_article(self, article: Dict) -> Dict:
        """Analyse un article et retourne les scores."""
        text = article.get('text', '')
        text_length = len(text)
        
        if not text or text_length < 100:
            return None
        
        # Filtrer franceculture.fr (média exclu)
        domain = article.get('domain', '')
        url = article.get('url', '')
        if domain == 'franceculture.fr' or 'franceculture.fr' in domain or 'franceculture.fr' in url:
            return None
        
        # Filtrer les articles publiés avant 2000 ou après 2025
        date_pub = article.get('date_pub', '')
        if self._is_article_date_invalid(date_pub, min_year=2000, max_year=2025):
            return None
        
        # Compter les occurrences avec pondération (nouveau format)
        if self.feminist_patterns_weighted:
            score_feministe = self._count_weighted_matches(text, self.feminist_patterns_weighted)
        else:
            # Fallback sur l'ancien format
            score_feministe = self._count_matches(text, self.feminist_patterns)
        
        # Plus de mots-clés équilibrants - score_balance toujours à 0
        score_balance = 0
        
        # L'indice militant est maintenant simplement égal au score féministe
        indice_militant = score_feministe
        
        # Calculer le pourcentage de militantisme basé UNIQUEMENT sur les mots-clés féministes
        # Formule: densité féministe normalisée (score féministe par rapport à la longueur du texte)
        # Cette métrique mesure l'intensité du militantisme sans comparaison avec les mots-clés équilibrants
        # On normalise sur une base de 1000 mots pour avoir un pourcentage comparable
        if text_length == 0:
            pct_militantisme = 0.0
        else:
            # Score féministe pour 1000 mots de texte
            score_per_1000_words = (score_feministe / text_length) * 1000
            # Convertir en pourcentage (on considère qu'un score de 10 pour 1000 mots = 100%)
            # Ajustez ce multiplicateur selon vos besoins
            pct_militantisme = min(100.0, score_per_1000_words * 10)  # Max 100%
        
        # Calculer les densités
        densite_feministe = self._calculate_density(score_feministe, text_length)
        densite_militant = self._calculate_density(abs(indice_militant), text_length)
        
        return {
            'url': article['url'],
            'domain': article.get('domain', ''),
            'date_pub': article.get('date_pub', ''),
            'text_length': text_length,
            'score_feministe': score_feministe,
            'score_balance': 0,  # Toujours 0 maintenant
            'indice_militant': indice_militant,
            'pct_militantisme': round(pct_militantisme, 1),
            'densite_feministe': round(densite_feministe, 3),
            'densite_balance': 0.0,  # Toujours 0 maintenant
            'densite_militant': round(densite_militant, 3),
            'analyze_date': datetime.now().isoformat()
        }
    
    def analyze_all(self):
        """Analyse tous les articles."""
        print("🔬 Début de l'analyse des articles...")
        
        if not self.articles_file.exists():
            print(f"❌ Fichier introuvable: {self.articles_file}")
            return
        
        # Charger les scores existants
        analyzed_urls = set()
        if self.scores_file.exists():
            with open(self.scores_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    analyzed_urls.add(row['url'])
        
        # Charger les articles
        articles_to_analyze = []
        with open(self.articles_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['url'] not in analyzed_urls:
                    articles_to_analyze.append(row)
        
        total = len(articles_to_analyze)
        print(f"📊 {total} articles à analyser")
        
        if total == 0:
            print("✅ Tous les articles ont déjà été analysés")
            return
        
        # Analyser les articles
        new_scores = []
        file_exists = self.scores_file.exists()
        
        for i, article in enumerate(articles_to_analyze, 1):
            print(f"[{i}/{total}] Analyse: {article.get('title', article['url'])[:60]}...")
            scores = self.analyze_article(article)
            
            if scores:
                new_scores.append(scores)
        
        # Sauvegarder les scores
        if new_scores:
            with open(self.scores_file, 'a', newline='', encoding='utf-8') as f:
                fieldnames = [
                    'url', 'domain', 'date_pub', 'text_length',
                    'score_feministe', 'score_balance', 'indice_militant',
                    'pct_militantisme',  # Nouveau champ
                    'densite_feministe', 'densite_balance', 'densite_militant',
                    'analyze_date'
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                if not file_exists:
                    writer.writeheader()
                
                writer.writerows(new_scores)
            
            print(f"\n✅ Analyse terminée: {len(new_scores)} articles analysés")
            
            # Afficher quelques statistiques
            if new_scores:
                avg_militant = sum(s['indice_militant'] for s in new_scores) / len(new_scores)
                print(f"📈 Indice militant moyen: {avg_militant:.2f}")
        else:
            print("\n✅ Tous les articles ont déjà été analysés")


def main():
    analyzer = ArticleAnalyzer()
    analyzer.analyze_all()


if __name__ == "__main__":
    main()

