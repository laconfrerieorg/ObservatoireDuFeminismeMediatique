#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script d'extraction du texte des articles HTML.
Parse les fichiers HTML téléchargés et extrait le titre, date et texte principal.
"""

import os
import sys
import csv
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

# Augmenter la limite de taille de champ CSV (défaut: 131072)
# Certains articles peuvent avoir des textes très longs
# Utiliser 50MB au lieu de sys.maxsize pour éviter l'erreur sur Windows
csv.field_size_limit(50 * 1024 * 1024)  # 50MB

sys.path.insert(0, str(Path(__file__).parent.parent))


class ArticleParser:
    """Parse les articles HTML et extrait le contenu textuel."""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / "data"
        self.raw_html_dir = self.data_dir / "raw_html"
        self.articles_file = self.data_dir / "articles_clean.csv"
        
        self.fetch_log_file = self.data_dir / "fetch_log.csv"
    
    def _load_fetch_log(self) -> Dict[str, str]:
        """Charge le log des téléchargements pour obtenir les chemins des fichiers."""
        log = {}
        if self.fetch_log_file.exists():
            with open(self.fetch_log_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['status'] == 'success':
                        log[row['url']] = row['file_path']
        return log
    
    def _extract_date_from_meta(self, soup: BeautifulSoup, url: str = "") -> Optional[str]:
        """Extrait la date de publication depuis les balises meta."""
        # Détecter le domaine pour utiliser des sélecteurs spécifiques
        domain = ""
        if url:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc.replace("www.", "").lower()
        
        # Balises meta communes pour les dates (ordre de priorité)
        date_selectors = [
            ('meta', {'property': 'article:published_time'}),
            ('meta', {'property': 'og:published_time'}),
            ('meta', {'property': 'article:published'}),
            ('meta', {'name': 'publication-date'}),
            ('meta', {'name': 'date'}),
            ('meta', {'name': 'publishdate'}),
            ('meta', {'name': 'DC.date'}),
            ('meta', {'name': 'DC.Date'}),
            ('meta', {'itemprop': 'datePublished'}),
            ('time', {'datetime': True}),
            ('time', {'itemprop': 'datePublished'}),
        ]
        
        # Sélecteurs spécifiques par domaine
        if 'lemonde.fr' in domain:
            date_selectors.insert(0, ('meta', {'property': 'article:published_time'}))
            date_selectors.insert(1, ('time', {'class': re.compile(r'date', re.I)}))
        elif 'france24.com' in domain:
            date_selectors.insert(0, ('meta', {'property': 'article:published_time'}))
            date_selectors.insert(1, ('time', {'class': re.compile(r'date|time', re.I)}))
        elif 'lefigaro.fr' in domain:
            date_selectors.insert(0, ('meta', {'property': 'article:published_time'}))
        elif 'liberation.fr' in domain:
            date_selectors.insert(0, ('meta', {'property': 'article:published_time'}))
            date_selectors.insert(1, ('time', {'class': re.compile(r'date', re.I)}))
        
        for tag_name, attrs in date_selectors:
            if tag_name == 'time':
                # Chercher toutes les balises time avec datetime
                time_tags = soup.find_all('time', attrs={'datetime': True})
                if not time_tags:
                    time_tags = soup.find_all('time', attrs)
                for time_tag in time_tags:
                    datetime_attr = time_tag.get('datetime')
                    if datetime_attr:
                        return datetime_attr
                    # Sinon, essayer le texte de la balise
                    text = time_tag.get_text(strip=True)
                    if text:
                        try:
                            parsed_date = date_parser.parse(text, fuzzy=True)
                            return parsed_date.isoformat()
                        except:
                            pass
            else:
                meta_tag = soup.find(tag_name, attrs)
                if meta_tag:
                    content = meta_tag.get('content') or meta_tag.get('datetime')
                    if content:
                        # Nettoyer et normaliser la date
                        try:
                            parsed_date = date_parser.parse(content, fuzzy=True)
                            return parsed_date.isoformat()
                        except:
                            return content
        
        return None
    
    def _extract_date_from_text(self, soup: BeautifulSoup) -> Optional[str]:
        """Tente d'extraire la date depuis le texte de la page."""
        # Chercher des patterns de date dans le texte
        date_patterns = [
            r'\d{1,2}[/-]\d{1,2}[/-]\d{4}',
            r'\d{4}[/-]\d{1,2}[/-]\d{1,2}',
            r'\d{1,2}\s+\w+\s+\d{4}',
        ]
        
        text = soup.get_text()
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            if matches:
                try:
                    # Essayer de parser la première date trouvée
                    date_str = matches[0]
                    parsed_date = date_parser.parse(date_str, fuzzy=True)
                    return parsed_date.isoformat()
                except:
                    pass
        
        return None
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extrait le titre de l'article."""
        # Ordre de priorité pour le titre
        title_selectors = [
            ('h1', {'class': re.compile(r'article|title|headline', re.I)}),
            ('meta', {'property': 'og:title'}),
            ('meta', {'name': 'title'}),
            ('title', {}),
        ]
        
        for tag_name, attrs in title_selectors:
            if tag_name == 'h1':
                h1 = soup.find('h1', attrs)
                if h1:
                    return h1.get_text(strip=True)
            else:
                meta = soup.find(tag_name, attrs)
                if meta:
                    content = meta.get('content') or meta.get_text(strip=True)
                    if content:
                        return content
        
        return ""
    
    def _extract_text(self, soup: BeautifulSoup, url: str = "") -> str:
        """Extrait le texte principal de l'article."""
        # Détecter le domaine pour utiliser des sélecteurs spécifiques
        domain = ""
        if url:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc.replace("www.", "").lower()
        
        # Sélecteurs spécifiques par domaine
        if 'france24.com' in domain:
            # Sélecteurs spécifiques pour France 24
            content_selectors = [
                ('article', {'class': re.compile(r'article|content', re.I)}),
                ('div', {'class': re.compile(r'article-content|article-body|article-text|content-body', re.I)}),
                ('div', {'class': re.compile(r'article__content|article__body', re.I)}),
                ('section', {'class': re.compile(r'article|content', re.I)}),
                ('div', {'data-module': re.compile(r'article', re.I)}),
                ('article', {}),
                ('main', {}),
            ]
        else:
            # Sélecteurs génériques pour les autres sites
            content_selectors = [
                ('article', {}),
                ('div', {'class': re.compile(r'article|content|post|text', re.I)}),
                ('main', {}),
                ('div', {'id': re.compile(r'article|content|post|text', re.I)}),
            ]
        
        content_element = None
        for tag_name, attrs in content_selectors:
            element = soup.find(tag_name, attrs)
            if element:
                content_element = element
                break
        
        if not content_element:
            # Fallback: prendre le body entier
            content_element = soup.find('body') or soup
        
        # Extraire tous les paragraphes et autres éléments de texte
        text_elements = content_element.find_all(['p', 'div', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li'], recursive=True)
        text_parts = []
        seen_texts = set()  # Éviter les doublons
        
        for elem in text_elements:
            text = elem.get_text(strip=True)
            # Filtrer les éléments trop courts (probablement du menu/nav)
            # Réduire le seuil à 30 caractères pour capturer plus de contenu
            if len(text) > 30 and text not in seen_texts:
                # Filtrer les textes qui ressemblent à des menus/navigation
                if not re.match(r'^(accueil|menu|navigation|recherche|connexion|inscription|partager|suivre|abonner)', text, re.I):
                    text_parts.append(text)
                    seen_texts.add(text)
        
        # Si toujours pas de texte, essayer d'extraire directement depuis le body
        if not text_parts or len('\n\n'.join(text_parts)) < 50:
            # Essayer d'extraire depuis les balises meta description
            meta_desc = soup.find('meta', {'name': re.compile(r'description', re.I)})
            if meta_desc and meta_desc.get('content'):
                text_parts.insert(0, meta_desc.get('content'))
            
            # Extraire le texte brut du body en dernier recours
            body_text = soup.find('body')
            if body_text:
                full_text = body_text.get_text(separator=' ', strip=True)
                # Nettoyer et diviser en phrases
                sentences = re.split(r'[.!?]\s+', full_text)
                for sentence in sentences:
                    sentence = sentence.strip()
                    if len(sentence) > 50 and sentence not in seen_texts:
                        text_parts.append(sentence)
                        seen_texts.add(sentence)
        
        return '\n\n'.join(text_parts)
    
    def parse_html_file(self, html_path: Path, url: str) -> Optional[Dict]:
        """Parse un fichier HTML et retourne les données extraites."""
        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Essayer avec d'autres encodages
            try:
                with open(html_path, 'r', encoding='latin-1') as f:
                    content = f.read()
            except:
                print(f"    ⚠️  Erreur d'encodage: {html_path}")
                return None
        
        # Vérifier si le contenu contient "Access Denied" ou des erreurs de blocage
        content_lower = content.lower()
        if 'access denied' in content_lower or 'accès refusé' in content_lower or 'access forbidden' in content_lower:
            print(f"    ⏭️  Access Denied détecté, article ignoré: {url}")
            return None
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Extraire les données
        title = self._extract_title(soup)
        text = self._extract_text(soup, url)
        
        # Extraire la date
        date_pub = self._extract_date_from_meta(soup, url)
        if not date_pub:
            date_pub = self._extract_date_from_text(soup)
        
        # Normaliser la date si elle existe et filtrer les articles avant 2000 ou après 2025
        if date_pub:
            try:
                parsed_date = date_parser.parse(date_pub, fuzzy=True)
                year = parsed_date.year
                # Filtrer les articles publiés avant 2000 ou après 2025
                if year < 2000:
                    print(f"    ⏭️  Article trop ancien ({year}): {url}")
                    return None
                if year > 2025:
                    print(f"    ⏭️  Article avec date future ({year}): {url}")
                    return None
                date_pub = parsed_date.isoformat()
            except:
                # Garder la date originale si le parsing échoue
                # Si on ne peut pas parser la date, on garde l'article (peut être récent)
                pass
        
        # Nettoyer le texte
        text = re.sub(r'\s+', ' ', text)  # Normaliser les espaces
        text = text.strip()
        
        # Réduire le seuil minimum à 50 caractères pour capturer plus d'articles
        # Certains articles peuvent être courts mais pertinents
        if not text or len(text) < 50:
            print(f"    ⚠️  Texte trop court ou vide: {url}")
            return None
        
        # Extraire le domaine et filtrer franceculture.fr
        domain = self._extract_domain(url)
        if domain == 'franceculture.fr' or 'franceculture.fr' in domain:
            print(f"    ⏭️  Article de franceculture.fr exclu: {url}")
            return None
        
        return {
            'url': url,
            'domain': domain,
            'title': title,
            'date_pub': date_pub or '',
            'text': text,
            'text_length': len(text),
            'parse_date': datetime.now().isoformat()
        }
    
    def _extract_domain(self, url: str) -> str:
        """Extrait le domaine d'une URL."""
        from urllib.parse import urlparse
        try:
            parsed = urlparse(url)
            return parsed.netloc.replace("www.", "")
        except:
            return ""
    
    def parse_all(self):
        """Parse tous les articles téléchargés."""
        print("📄 Début du parsing des articles...")
        
        # Charger le log des téléchargements
        fetch_log = self._load_fetch_log()
        
        if not fetch_log:
            print("❌ Aucun article téléchargé trouvé")
            return
        
        # Charger les articles déjà parsés
        parsed_urls = set()
        if self.articles_file.exists():
            with open(self.articles_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    parsed_urls.add(row['url'])
        
        # Parser les nouveaux articles
        file_exists = self.articles_file.exists()
        new_articles = []
        
        total = len(fetch_log)
        current = 0
        
        for url, file_path in fetch_log.items():
            current += 1
            
            if url in parsed_urls:
                continue
            
            html_path = self.base_dir / file_path
            if not html_path.exists():
                continue
            
            print(f"[{current}/{total}] Parsing: {url[:60]}...")
            article_data = self.parse_html_file(html_path, url)
            
            if article_data:
                new_articles.append(article_data)
        
        # Sauvegarder les nouveaux articles
        if new_articles:
            with open(self.articles_file, 'a', newline='', encoding='utf-8') as f:
                fieldnames = ['url', 'domain', 'title', 'date_pub', 'text', 'text_length', 'parse_date']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                if not file_exists:
                    writer.writeheader()
                
                writer.writerows(new_articles)
            
            print(f"\n✅ Parsing terminé: {len(new_articles)} nouveaux articles parsés")
        else:
            print("\n✅ Tous les articles ont déjà été parsés")


def main():
    parser = ArticleParser()
    parser.parse_all()


if __name__ == "__main__":
    main()

