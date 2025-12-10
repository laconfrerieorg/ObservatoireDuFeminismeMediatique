# 🔄 Guide de réinitialisation

Ce guide explique comment réinitialiser complètement les données et relancer le pipeline avec les nouveaux médias configurés.

## 📋 Étapes de réinitialisation

### 1. Réinitialiser toutes les données

Exécutez le script de réinitialisation :

```bash
python scripts/reset_data.py
```

Ce script va :
- ✅ Supprimer tous les fichiers CSV (URLs, articles, scores, stats)
- ✅ Supprimer le dossier `raw_html/` avec tous les articles téléchargés
- ✅ Recréer les dossiers nécessaires

**⚠️ Attention :** Cette opération est irréversible. Toutes les données collectées seront perdues.

### 2. Vérifier la configuration des médias

Le fichier `config/medias.yml` contient maintenant les médias suivants :

- Le Monde (lemonde.fr)
- France 24 (france24.com)
- 20 Minutes (20minutes.fr)
- Le Figaro (lefigaro.fr)
- Les Echos (lesechos.fr)
- Libération (liberation.fr)
- La Croix (la-croix.com)
- Le Parisien (leparisien.fr)
- La Dépêche (ladepeche.fr)
- L'Obs (nouvelobs.com)

Vous pouvez modifier cette liste si nécessaire.

### 3. Relancer le pipeline complet

Une fois les données réinitialisées, relancez le pipeline étape par étape :

```bash
# 1. Collecter les URLs depuis les moteurs de recherche
python scripts/collect_urls.py

# 2. Télécharger les articles HTML
python scripts/fetch_articles.py

# 3. Parser les articles (extraire le texte)
python scripts/parse_articles.py

# 4. Analyser les articles (calculer les scores)
python scripts/analyze_articles.py

# 5. Générer les statistiques
python scripts/build_stats.py
```

### 4. Lancer le dashboard

Pour visualiser les résultats :

```bash
python app/api.py
```

Puis ouvrez votre navigateur sur : `http://localhost:5000`

## 🔧 Configuration Playwright

Certains sites nécessitent Playwright pour contourner les protections anti-bot :
- `lemonde.fr`
- `france24.com`

Si vous rencontrez des erreurs 403/406 sur d'autres sites, vous pouvez les ajouter dans `scripts/fetch_articles.py` à la ligne 68 :

```python
self.use_playwright_for = {'france24.com', 'lemonde.fr', 'autre-site.com'}
```

## 📊 Temps estimé

Selon le nombre de médias et de mots-clés :
- **Collecte d'URLs** : 10-30 minutes (selon le nombre de recherches)
- **Téléchargement** : 30-60 minutes (selon le nombre d'articles)
- **Parsing** : 5-10 minutes
- **Analyse** : 2-5 minutes
- **Stats** : < 1 minute

**Total estimé :** 1-2 heures pour une collecte complète.

## ⚠️ Notes importantes

1. **Respect des robots.txt** : Le script respecte les délais entre requêtes pour ne pas surcharger les serveurs.

2. **Playwright requis** : Assurez-vous d'avoir installé Playwright et ses navigateurs :
   ```bash
   pip install playwright
   playwright install chromium
   ```

3. **Espace disque** : Les articles HTML peuvent prendre de l'espace. Surveillez le dossier `data/raw_html/`.

4. **Erreurs attendues** : Certains articles peuvent échouer (404, 403, etc.). C'est normal et le script continue.

## 🆘 En cas de problème

Si vous rencontrez des erreurs :

1. Vérifiez que tous les médias dans `config/medias.yml` ont le bon format
2. Vérifiez que Playwright est installé si nécessaire
3. Vérifiez les logs dans `data/fetch_log.csv` pour voir les erreurs de téléchargement
4. Relancez uniquement les étapes qui ont échoué

