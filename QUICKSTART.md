# 🚀 Guide de démarrage rapide

## Installation en 3 étapes

### 1. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 1bis. Installer Playwright (recommandé pour contourner les protections anti-bot)

```bash
playwright install chromium
```

**Note** : Playwright est utilisé automatiquement pour les sites avec protection anti-bot (France 24, Le Monde). Si non installé, le script utilisera `requests` en fallback.

### 2. Configuration (optionnel)

Si vous voulez utiliser SerpAPI ou Bing API au lieu de DuckDuckGo :

1. Créez un fichier `.env` à la racine du projet
2. Copiez le contenu de `env.example.txt` dans `.env`
3. Ajoutez vos clés API

**Note** : Par défaut, DuckDuckGo est utilisé et ne nécessite pas de clé API.

### 3. Lancer le pipeline

**Sur Windows :**
```bash
run_pipeline.bat
```

**Sur Linux/Mac :**
```bash
python scripts/run_pipeline.py
```

**Ou manuellement, étape par étape :**
```bash
python scripts/collect_urls.py      # 1. Collecte des URLs
python scripts/fetch_articles.py     # 2. Téléchargement
python scripts/parse_articles.py     # 3. Parsing
python scripts/analyze_articles.py   # 4. Analyse
python scripts/build_stats.py        # 5. Statistiques
```

## Visualiser les résultats

**Sur Windows :**
```bash
start_dashboard.bat
```

**Sur Linux/Mac :**
```bash
python app/api.py
```

Puis ouvrez votre navigateur à : **http://localhost:5000**

## ⚙️ Personnalisation

### Ajouter un média

Éditez `config/medias.yml` :

```yaml
medias:
  - name: "Votre média"
    domain: "votredomaine.fr"
```

### Ajouter des mots-clés

Éditez `config/keywords.yml` et ajoutez vos mots-clés dans les sections :
- `feminist_keywords` : Mots-clés du narratif féministe
- `balanced_keywords` : Mots-clés équilibrants (sources neutres, etc.)

## 🔄 Automatisation

Pour exécuter le pipeline automatiquement chaque jour, créez une tâche planifiée (Windows) ou un cron job (Linux) :

**Windows (Tâche planifiée) :**
- Ouvrez le Planificateur de tâches
- Créez une tâche qui exécute `run_pipeline.bat` chaque jour à 3h du matin

**Linux (Cron) :**
```bash
# Éditez le crontab
crontab -e

# Ajoutez cette ligne (exécution chaque jour à 3h)
0 3 * * * cd /chemin/vers/observatoire_medias && python scripts/run_pipeline.py
```

## 📊 Comprendre les résultats

- **Indice militant positif** : L'article utilise plus de mots-clés féministes que de mots-clés équilibrants
- **Indice militant négatif** : L'article mentionne des sources équilibrantes ou les victimes masculines
- **Indice militant proche de zéro** : Équilibre entre les deux narratifs

## ❓ Problèmes courants

### "ModuleNotFoundError: No module named 'ddgs'"

Installez la dépendance manquante :
```bash
pip install ddgs
```

### "Aucune statistique disponible" dans le dashboard

Exécutez d'abord le pipeline complet pour générer les données :
```bash
python scripts/run_pipeline.py
```

### Les recherches ne retournent rien

- Vérifiez votre connexion internet
- Si vous utilisez une API payante, vérifiez votre clé dans `.env`
- Augmentez les délais dans `scripts/collect_urls.py` (ligne `time.sleep(1)`)

## 📝 Notes importantes

- Le premier lancement peut prendre du temps (collecte de nombreuses URLs)
- Les scripts gèrent automatiquement les doublons
- Les données sont stockées dans le dossier `data/`
- Le dashboard se met à jour automatiquement toutes les 5 minutes

