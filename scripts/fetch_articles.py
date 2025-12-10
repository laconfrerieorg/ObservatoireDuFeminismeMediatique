#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de téléchargement des articles HTML.
Télécharge les pages web des URLs collectées et les stocke localement.
"""

import os
import sys
import csv
import hashlib
import time
import yaml
import asyncio
import aiohttp
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
import requests
from urllib.parse import urlparse
from collections import defaultdict

# Essayer d'importer Playwright (version asynchrone)
try:
    from playwright.async_api import async_playwright, Browser, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    try:
        from playwright.sync_api import sync_playwright, Browser, Page
        PLAYWRIGHT_AVAILABLE = False
        PLAYWRIGHT_SYNC_ONLY = True
    except ImportError:
        PLAYWRIGHT_AVAILABLE = False
        PLAYWRIGHT_SYNC_ONLY = False
        print("⚠️  Playwright non installé. Installez-le avec: pip install playwright && playwright install chromium")

sys.path.insert(0, str(Path(__file__).parent.parent))


class ArticleFetcher:
    """Télécharge et stocke les articles HTML."""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.config_dir = self.base_dir / "config"
        self.data_dir = self.base_dir / "data"
        self.raw_html_dir = self.data_dir / "raw_html"
        self.raw_html_dir.mkdir(parents=True, exist_ok=True)
        
        self.urls_clean_file = self.data_dir / "urls_clean.csv"
        self.fetch_log_file = self.data_dir / "fetch_log.csv"
        
        # Charger la configuration des médias pour filtrer les URLs
        self.medias = self._load_medias_config()
        
        # Session requests pour les sites qui ne bloquent pas (fallback)
        self.session = requests.Session()
        # En-têtes HTTP réalistes pour simuler un navigateur réel
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        })
        
        # Playwright pour les sites avec protection anti-bot
        self.playwright = None
        self.browser = None
        self.use_playwright_for = {'france24.com', 'lemonde.fr', 'lesechos.fr'}  # Sites nécessitant Playwright
        
        # Limites de rate par domaine (pour éviter de surcharger)
        self.domain_delays = {
            'lemonde.fr': 1.0,  # 1 seconde entre requêtes
            'france24.com': 1.0,
            'default': 0.5  # 0.5 seconde par défaut
        }
        
        # Dernière requête par domaine (pour respecter les délais)
        self.domain_last_request = defaultdict(float)
    
    def _load_medias_config(self) -> Dict:
        """Charge la configuration des médias."""
        config_path = self.config_dir / "medias.yml"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {'medias': []}
    
    def _extract_domain(self, url: str) -> str:
        """Extrait le domaine d'une URL."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.replace("www.", "")
            return domain
        except:
            return ""
    
    def _is_allowed_domain(self, url: str) -> bool:
        """Vérifie si l'URL appartient à un média configuré."""
        domain = self._extract_domain(url)
        allowed_domains = {media['domain'] for media in self.medias.get('medias', [])}
        return domain in allowed_domains if allowed_domains else True  # Si aucun média configuré, tout accepter
    
    async def _init_playwright_async(self):
        """Initialise Playwright en mode asynchrone si disponible."""
        if not PLAYWRIGHT_AVAILABLE:
            return False
        
        if self.playwright is None:
            try:
                self.playwright = await async_playwright().start()
                # Lancer le navigateur en mode headless
                self.browser = await self.playwright.chromium.launch(
                    headless=True,
                    args=['--disable-blink-features=AutomationControlled']
                )
                return True
            except Exception as e:
                print(f"⚠️  Erreur lors de l'initialisation de Playwright: {e}")
                return False
        return True
    
    def _init_playwright(self):
        """Initialise Playwright en mode synchrone (fallback)."""
        if PLAYWRIGHT_SYNC_ONLY:
            if self.playwright is None:
                try:
                    self.playwright = sync_playwright().start()
                    self.browser = self.playwright.chromium.launch(
                        headless=True,
                        args=['--disable-blink-features=AutomationControlled']
                    )
                    return True
                except Exception as e:
                    print(f"⚠️  Erreur lors de l'initialisation de Playwright: {e}")
                    return False
            return True
        return False
    
    async def _close_playwright_async(self):
        """Ferme Playwright en mode asynchrone avec nettoyage complet."""
        if self.browser:
            try:
                # Fermer tous les contextes ouverts
                contexts = self.browser.contexts
                for context in contexts:
                    try:
                        await context.close()
                    except:
                        pass
                # Fermer le navigateur
                await self.browser.close()
                # Attendre un peu pour que les processus se terminent
                await asyncio.sleep(0.5)
            except Exception as e:
                # Ignorer les erreurs de fermeture
                pass
        if self.playwright:
            try:
                await self.playwright.stop()
                # Attendre un peu pour que les processus se terminent
                await asyncio.sleep(0.5)
            except Exception as e:
                # Ignorer les erreurs de fermeture
                pass
        self.browser = None
        self.playwright = None
    
    def _close_playwright(self):
        """Ferme Playwright en mode synchrone."""
        if self.browser:
            try:
                self.browser.close()
            except:
                pass
        if self.playwright:
            try:
                self.playwright.stop()
            except:
                pass
        self.browser = None
        self.playwright = None
    
    async def _fetch_with_playwright_async(self, url: str) -> Optional[str]:
        """Télécharge une URL avec Playwright en mode asynchrone."""
        if not await self._init_playwright_async():
            return None
        
        try:
            # Créer un nouveau contexte de navigation
            context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='fr-FR',
                timezone_id='Europe/Paris',
            )
            page = await context.new_page()
            
            # Naviguer vers la page
            await page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Attendre un peu pour que le JavaScript se charge
            await page.wait_for_timeout(2000)
            
            # Récupérer le HTML
            html_content = await page.content()
            
            # Fermer le contexte
            await page.close()
            await context.close()
            
            return html_content
        
        except Exception as e:
            print(f"    ⚠️  Erreur Playwright: {str(e)}")
            return None
    
    def _fetch_with_playwright(self, url: str) -> Optional[str]:
        """Télécharge une URL avec Playwright en mode synchrone (fallback)."""
        if not self._init_playwright():
            return None
        
        try:
            context = self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='fr-FR',
                timezone_id='Europe/Paris',
            )
            page = context.new_page()
            page.goto(url, wait_until='networkidle', timeout=30000)
            page.wait_for_timeout(2000)
            html_content = page.content()
            page.close()
            context.close()
            return html_content
        except Exception as e:
            print(f"    ⚠️  Erreur Playwright: {str(e)}")
            return None
    
    def _url_to_hash(self, url: str) -> str:
        """Génère un hash MD5 de l'URL pour le nom de fichier."""
        return hashlib.md5(url.encode('utf-8')).hexdigest()
    
    def _get_file_path(self, url: str) -> Path:
        """Retourne le chemin du fichier HTML pour une URL."""
        url_hash = self._url_to_hash(url)
        # Structure: raw_html/ab/cdef1234.html (2 premiers caractères = sous-dossier)
        subdir = self.raw_html_dir / url_hash[:2]
        subdir.mkdir(exist_ok=True)
        return subdir / f"{url_hash}.html"
    
    def _is_already_fetched(self, url: str) -> bool:
        """Vérifie si l'URL a déjà été téléchargée."""
        file_path = self._get_file_path(url)
        return file_path.exists()
    
    def _load_fetch_log(self) -> Dict[str, Dict]:
        """Charge le log des téléchargements."""
        log = {}
        if self.fetch_log_file.exists():
            with open(self.fetch_log_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    log[row['url']] = row
        return log
    
    def _save_fetch_log(self, url: str, status: str, error: str = ""):
        """Enregistre le résultat du téléchargement dans le log."""
        file_exists = self.fetch_log_file.exists()
        
        with open(self.fetch_log_file, 'a', newline='', encoding='utf-8') as f:
            fieldnames = ['url', 'status', 'error', 'fetch_date', 'file_path']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
            
            file_path = self._get_file_path(url)
            writer.writerow({
                'url': url,
                'status': status,
                'error': error[:200] if error else '',  # Limiter la taille
                'fetch_date': datetime.now().isoformat(),
                'file_path': str(file_path.relative_to(self.base_dir))
            })
    
    async def _wait_for_domain_rate_limit(self, domain: str):
        """Attend si nécessaire pour respecter le rate limiting par domaine."""
        delay = self.domain_delays.get(domain, self.domain_delays['default'])
        last_request = self.domain_last_request[domain]
        elapsed = time.time() - last_request
        
        if elapsed < delay:
            await asyncio.sleep(delay - elapsed)
        
        self.domain_last_request[domain] = time.time()
    
    async def fetch_url_async(self, session: aiohttp.ClientSession, url: str) -> bool:
        """Télécharge une URL de manière asynchrone."""
        # Vérifier si déjà téléchargé
        if self._is_already_fetched(url):
            return True
        
        try:
            # Extraire le domaine
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.replace("www.", "")
            
            # Respecter le rate limiting par domaine
            await self._wait_for_domain_rate_limit(domain)
            
            # Utiliser Playwright pour les sites avec protection anti-bot
            if domain in self.use_playwright_for and PLAYWRIGHT_AVAILABLE:
                html_content = await self._fetch_with_playwright_async(url)
                if html_content:
                    file_path = self._get_file_path(url)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                    self._save_fetch_log(url, 'success')
                    return True
            
            # Utiliser aiohttp pour les autres sites
            domain_full = f"{parsed_url.scheme}://{parsed_url.netloc}"
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}/"
            
            headers = {
                'Referer': base_url,
                'Origin': domain_full,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            }
            
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15), allow_redirects=True) as response:
                # Gérer les erreurs 403 et 406
                if response.status in [403, 406]:
                    if PLAYWRIGHT_AVAILABLE:
                        html_content = await self._fetch_with_playwright_async(url)
                        if html_content:
                            file_path = self._get_file_path(url)
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(html_content)
                            self._save_fetch_log(url, 'success')
                            return True
                    self._save_fetch_log(url, 'error', f"HTTP {response.status}: Site bloque les requêtes automatisées")
                    return False
                
                response.raise_for_status()
                
                # Vérifier le Content-Type
                content_type = response.headers.get('Content-Type', '').lower()
                if 'text/html' not in content_type:
                    self._save_fetch_log(url, 'skipped', f"Non-HTML: {content_type}")
                    return False
                
                # Sauvegarder le HTML
                html_content = await response.read()
                
                # Vérifier si le contenu contient "Access Denied" ou des erreurs de blocage
                html_text = html_content.decode('utf-8', errors='ignore').lower()
                if 'access denied' in html_text or 'accès refusé' in html_text or 'access forbidden' in html_text:
                    # Réessayer avec Playwright si disponible
                    if PLAYWRIGHT_AVAILABLE:
                        print(f"    ⚠️  Access Denied détecté, tentative avec Playwright...")
                        html_content_playwright = await self._fetch_with_playwright_async(url)
                        if html_content_playwright and 'access denied' not in html_content_playwright.lower():
                            file_path = self._get_file_path(url)
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(html_content_playwright)
                            self._save_fetch_log(url, 'success')
                            return True
                    self._save_fetch_log(url, 'error', 'Access Denied - Site bloque l\'accès')
                    return False
                
                file_path = self._get_file_path(url)
                with open(file_path, 'wb') as f:
                    f.write(html_content)
                
                self._save_fetch_log(url, 'success')
                return True
        
        except asyncio.TimeoutError:
            self._save_fetch_log(url, 'error', 'Timeout')
            return False
        except aiohttp.ClientError as e:
            error_msg = str(e)
            self._save_fetch_log(url, 'error', error_msg)
            return False
        except Exception as e:
            error_msg = str(e)
            self._save_fetch_log(url, 'error', error_msg)
            return False
    
    def fetch_url(self, url: str) -> bool:
        """Télécharge une URL et sauvegarde le HTML."""
        # Vérifier si déjà téléchargé
        if self._is_already_fetched(url):
            return True
        
        try:
            print(f"  📥 Téléchargement: {url[:80]}...")
            
            # Extraire le domaine
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.replace("www.", "")
            
            # Utiliser Playwright pour les sites avec protection anti-bot
            if domain in self.use_playwright_for and PLAYWRIGHT_AVAILABLE:
                html_content = self._fetch_with_playwright(url)
                if html_content:
                    # Sauvegarder le HTML
                    file_path = self._get_file_path(url)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                    self._save_fetch_log(url, 'success')
                    return True
                else:
                    # Fallback sur requests si Playwright échoue
                    print(f"    ⚠️  Playwright a échoué, tentative avec requests...")
            
            # Utiliser requests pour les autres sites ou en fallback
            domain_full = f"{parsed_url.scheme}://{parsed_url.netloc}"
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}/"
            
            # En-têtes spécifiques pour cette requête (plus réalistes)
            headers = {
                'Referer': base_url,  # Simuler une navigation depuis la page d'accueil
                'Origin': domain_full,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
            }
            
            response = self.session.get(url, headers=headers, timeout=15, allow_redirects=True)
            
            # Gérer spécifiquement les erreurs 403 et 406
            if response.status_code in [403, 406]:
                # Si erreur 403/406 et Playwright disponible, l'utiliser
                if PLAYWRIGHT_AVAILABLE:
                    print(f"    ⚠️  Erreur {response.status_code}, tentative avec Playwright...")
                    html_content = self._fetch_with_playwright(url)
                    if html_content:
                        file_path = self._get_file_path(url)
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(html_content)
                        self._save_fetch_log(url, 'success')
                        return True
                else:
                    # Essayer d'abord d'accéder à la page d'accueil pour obtenir des cookies
                    try:
                        self.session.get(base_url, timeout=10)
                        time.sleep(1)  # Petite pause
                    except:
                        pass
                    
                    # Réessayer avec des en-têtes encore plus réalistes
                    headers.update({
                        'Referer': base_url,
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'Accept-Language': 'fr-FR,fr;q=0.9',
                        'Sec-Fetch-Dest': 'document',
                        'Sec-Fetch-Mode': 'navigate',
                        'Sec-Fetch-Site': 'same-origin',
                        'Sec-Fetch-User': '?1',
                    })
                    response = self.session.get(url, headers=headers, timeout=15, allow_redirects=True)
            
            response.raise_for_status()
            
            # Vérifier le Content-Type
            content_type = response.headers.get('Content-Type', '').lower()
            if 'text/html' not in content_type:
                print(f"    ⚠️  Type de contenu non-HTML: {content_type}")
                self._save_fetch_log(url, 'skipped', f"Non-HTML: {content_type}")
                return False
            
            # Vérifier si le contenu contient "Access Denied" ou des erreurs de blocage
            html_text = response.text.lower()
            if 'access denied' in html_text or 'accès refusé' in html_text or 'access forbidden' in html_text:
                # Réessayer avec Playwright si disponible
                if PLAYWRIGHT_AVAILABLE:
                    print(f"    ⚠️  Access Denied détecté, tentative avec Playwright...")
                    html_content = self._fetch_with_playwright(url)
                    if html_content and 'access denied' not in html_content.lower():
                        file_path = self._get_file_path(url)
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(html_content)
                        self._save_fetch_log(url, 'success')
                        return True
                self._save_fetch_log(url, 'error', 'Access Denied - Site bloque l\'accès')
                return False
            
            # Sauvegarder le HTML
            file_path = self._get_file_path(url)
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            self._save_fetch_log(url, 'success')
            return True
        
        except requests.exceptions.Timeout:
            error_msg = "Timeout"
            print(f"    ❌ Timeout: {url}")
            self._save_fetch_log(url, 'error', error_msg)
            return False
        
        except requests.exceptions.HTTPError as e:
            # Gérer spécifiquement les erreurs HTTP
            status_code = e.response.status_code if hasattr(e, 'response') else None
            if status_code == 403:
                error_msg = "403 Forbidden - Site bloque les requêtes automatisées (protection anti-bot)"
                print(f"    ⚠️  {error_msg}")
            elif status_code == 406:
                error_msg = "406 Not Acceptable - Site bloque les requêtes automatisées"
                print(f"    ⚠️  {error_msg}")
            else:
                error_msg = f"HTTP {status_code}: {str(e)}"
                print(f"    ❌ Erreur: {error_msg}")
            self._save_fetch_log(url, 'error', error_msg)
            return False
        
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            print(f"    ❌ Erreur: {error_msg}")
            self._save_fetch_log(url, 'error', error_msg)
            return False
        
        except Exception as e:
            error_msg = str(e)
            print(f"    ❌ Erreur inattendue: {error_msg}")
            self._save_fetch_log(url, 'error', error_msg)
            return False
    
    async def fetch_all_async(self, max_concurrent: int = 10):
        """Télécharge tous les articles depuis urls_clean.csv de manière asynchrone."""
        if not self.urls_clean_file.exists():
            print(f"❌ Fichier introuvable: {self.urls_clean_file}")
            return
        
        print("📥 Début du téléchargement des articles (mode asynchrone)...")
        
        # Charger le log existant
        fetch_log = self._load_fetch_log()
        already_processed = {url for url, log in fetch_log.items() if log['status'] == 'success'}
        
        urls_to_fetch = []
        allowed_domains = {media['domain'] for media in self.medias.get('medias', [])}
        ignored_count = 0
        ignored_domains = {}
        
        with open(self.urls_clean_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                url = row['url']
                # Filtrer par domaine si des médias sont configurés
                if url not in already_processed:
                    if not allowed_domains or self._is_allowed_domain(url):
                        urls_to_fetch.append(url)
                    else:
                        # Compter les URLs ignorées par domaine
                        ignored_count += 1
                        domain = self._extract_domain(url)
                        ignored_domains[domain] = ignored_domains.get(domain, 0) + 1
        
        total = len(urls_to_fetch)
        if ignored_count > 0:
            print(f"⏭️  {ignored_count} URLs ignorées (domaines non configurés):")
            for domain, count in sorted(ignored_domains.items()):
                print(f"   - {domain}: {count} URL(s)")
        print(f"📊 {total} URLs à télécharger (domaines autorisés: {', '.join(allowed_domains) if allowed_domains else 'tous'})")
        print(f"🚀 Téléchargement en parallèle (max {max_concurrent} connexions simultanées)...\n")
        
        if total == 0:
            print("✅ Toutes les URLs ont déjà été téléchargées")
            return
        
        # Créer une session aiohttp avec nettoyage automatique
        connector = aiohttp.TCPConnector(
            limit=max_concurrent, 
            limit_per_host=3,
            force_close=True,  # Forcer la fermeture des connexions
            enable_cleanup_closed=True  # Nettoyer les connexions fermées
        )
        timeout = aiohttp.ClientTimeout(total=30)
        
        success_count = 0
        error_count = 0
        completed = 0
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            # Créer un sémaphore pour limiter le nombre de requêtes simultanées
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def fetch_with_semaphore(url):
                nonlocal success_count, error_count, completed
                async with semaphore:
                    completed += 1
                    print(f"[{completed}/{total}]", end=" ")
                    print(f"📥 {url[:60]}...")
                    
                    result = await self.fetch_url_async(session, url)
                    if result:
                        success_count += 1
                    else:
                        error_count += 1
            
            # Créer toutes les tâches
            tasks = [fetch_with_semaphore(url) for url in urls_to_fetch]
            
            # Exécuter toutes les tâches
            await asyncio.gather(*tasks)
            
            # Attendre que toutes les connexions soient fermées avant la sortie du context manager
            await asyncio.sleep(0.5)
        
        print(f"\n✅ Téléchargement terminé:")
        print(f"   ✅ Succès: {success_count}")
        print(f"   ❌ Erreurs: {error_count}")
        
        # Fermer Playwright à la fin avec nettoyage complet
        try:
            await self._close_playwright_async()
        except Exception as e:
            # Ignorer les erreurs de fermeture
            pass
        
        # Attendre un peu pour que toutes les ressources soient libérées
        await asyncio.sleep(1)
    
    def fetch_all(self):
        """Télécharge tous les articles depuis urls_clean.csv (mode synchrone - fallback)."""
        if not self.urls_clean_file.exists():
            print(f"❌ Fichier introuvable: {self.urls_clean_file}")
            return
        
        print("📥 Début du téléchargement des articles...")
        
        # Charger le log existant
        fetch_log = self._load_fetch_log()
        already_processed = {url for url, log in fetch_log.items() if log['status'] == 'success'}
        
        urls_to_fetch = []
        allowed_domains = {media['domain'] for media in self.medias.get('medias', [])}
        ignored_count = 0
        ignored_domains = {}
        
        with open(self.urls_clean_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                url = row['url']
                # Filtrer par domaine si des médias sont configurés
                if url not in already_processed:
                    if not allowed_domains or self._is_allowed_domain(url):
                        urls_to_fetch.append(url)
                    else:
                        # Compter les URLs ignorées par domaine
                        ignored_count += 1
                        domain = self._extract_domain(url)
                        ignored_domains[domain] = ignored_domains.get(domain, 0) + 1
        
        total = len(urls_to_fetch)
        if ignored_count > 0:
            print(f"⏭️  {ignored_count} URLs ignorées (domaines non configurés):")
            for domain, count in sorted(ignored_domains.items()):
                print(f"   - {domain}: {count} URL(s)")
        print(f"📊 {total} URLs à télécharger (domaines autorisés: {', '.join(allowed_domains) if allowed_domains else 'tous'})")
        
        if total == 0:
            print("✅ Toutes les URLs ont déjà été téléchargées")
            return
        
        success_count = 0
        error_count = 0
        
        for i, url in enumerate(urls_to_fetch, 1):
            print(f"[{i}/{total}]", end=" ")
            if self.fetch_url(url):
                success_count += 1
            else:
                error_count += 1
            
            # Pause pour respecter les robots.txt et éviter de surcharger
            # Délai plus long pour les sites stricts
            parsed_url = urlparse(url)
            if 'lemonde.fr' in parsed_url.netloc:
                time.sleep(3)  # 3 secondes pour Le Monde
            elif 'france24.com' in parsed_url.netloc:
                time.sleep(3)  # 3 secondes pour France 24 (protection anti-bot)
            elif 'lesechos.fr' in parsed_url.netloc:
                time.sleep(3)  # 3 secondes pour Les Echos (protection anti-bot)
            else:
                time.sleep(2)  # 2 secondes pour les autres sites
        
        print(f"\n✅ Téléchargement terminé:")
        print(f"   ✅ Succès: {success_count}")
        print(f"   ❌ Erreurs: {error_count}")
        
        # Fermer Playwright à la fin
        self._close_playwright()


async def main_async():
    """Point d'entrée asynchrone."""
    fetcher = ArticleFetcher()
    try:
        await fetcher.fetch_all_async(max_concurrent=10)
    finally:
        # S'assurer que Playwright est fermé même en cas d'erreur
        try:
            await fetcher._close_playwright_async()
        except:
            pass

def main():
    """Point d'entrée principal (utilise asyncio si disponible)."""
    try:
        # Utiliser asyncio.run() qui gère mieux la fermeture sur Windows
        asyncio.run(main_async())
        # Petite pause supplémentaire pour laisser le temps aux ressources de se libérer
        import sys
        if sys.platform == 'win32':
            time.sleep(0.5)
    except RuntimeError as e:
        # Fallback sur le mode synchrone si asyncio n'est pas disponible
        print("⚠️  Mode asynchrone non disponible, utilisation du mode synchrone...")
        fetcher = ArticleFetcher()
        fetcher.fetch_all()
    except KeyboardInterrupt:
        print("\n⚠️  Interruption par l'utilisateur")
        sys.exit(1)


if __name__ == "__main__":
    main()

