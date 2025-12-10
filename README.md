# 🔬 Observatoire des médias

Analyse automatique du narratif féministe dans les médias français.

## 📋 Description

Cet observatoire mesure automatiquement à quel point les médias reprennent le narratif féministe militant, article par article, puis média par média. Il collecte les articles, analyse leur contenu et génère des statistiques visuelles via un dashboard web.

## 🏗️ Architecture

Le projet suit un pipeline en 4 étapes :

1. **Collecte d'URLs** : Recherche d'articles via moteurs de recherche
2. **Récupération** : Téléchargement et stockage du HTML
3. **Parsing** : Extraction du texte et métadonnées
4. **Analyse** : Calcul des scores idéologiques et génération de statistiques

## 📁 Structure du projet

```
observatoire_medias/
├── config/
│   ├── medias.yml              # Liste des médias & domaines
│   ├── keywords.yml            # Mots-clés féministes / équilibrants
│   └── search_providers.yml    # Configuration des APIs de recherche
├── data/
│   ├── urls_raw.csv            # URLs brutes collectées
│   ├── urls_clean.csv          # URLs uniques
│   ├── raw_html/               # HTML brut téléchargé
│   ├── articles_clean.csv      # Articles parsés
│   ├── scores.csv              # Scores par article
│   ├── stats_daily.json        # Statistiques agrégées
│   └── fetch_log.csv           # Log des téléchargements
├── scripts/
│   ├── collect_urls.py         # Collecte d'URLs
│   ├── fetch_articles.py       # Téléchargement HTML
│   ├── parse_articles.py       # Extraction du texte
│   ├── analyze_articles.py     # Calcul des scores
│   ├── build_stats.py          # Génération des stats
│   ├── run_pipeline.py         # Script d'orchestration du pipeline complet
│   ├── reset_data.py           # Réinitialisation des données
│   ├── audit_parsing.py        # Audit de qualité du parsing
│   ├── test_sensitivity.py     # Tests de sensibilité des mots-clés
│   ├── filter_old_articles.py  # Filtrage des articles par date
│   ├── remove_duplicates.py    # Suppression des doublons
│   ├── statistical_tests.py    # Tests statistiques
│   └── validation_inter_codage.py # Validation inter-codage
├── app/
│   ├── api.py                  # API Flask
│   └── static/
│       ├── index.html          # Dashboard frontend
│       ├── app.js              # Application JavaScript
│       └── style.css           # Styles CSS
├── env.example.txt             # Exemple de configuration (à copier en .env)
├── run_pipeline.bat            # Script batch Windows pour lancer le pipeline
├── start_dashboard.bat         # Script batch Windows pour lancer le dashboard
├── requirements.txt            # Dépendances Python
├── README.md                   # Ce fichier
├── QUICKSTART.md               # Guide de démarrage rapide
├── METHODOLOGIE.md             # Documentation méthodologique
└── RESET_GUIDE.md              # Guide de réinitialisation
```

## 🚀 Installation

### 1. Cloner ou télécharger le projet

```bash
cd "Observatoire media"
```

### 2. Installer les dépendances Python

```bash
pip install -r requirements.txt
```

### 2bis. Installer les navigateurs Playwright (recommandé)

Pour contourner les protections anti-bot (notamment France 24), Playwright est utilisé automatiquement :

```bash
playwright install chromium
```

**Note** : Si Playwright n'est pas installé, le script utilisera `requests` en fallback, mais certains sites peuvent bloquer les requêtes automatisées.

### 3. Configuration

Copiez `env.example.txt` vers `.env` et configurez vos clés API si nécessaire :

**Sur Windows :**
```bash
copy env.example.txt .env
```

**Sur Linux/Mac :**
```bash
cp env.example.txt .env
```

**Note** : Par défaut, le script utilise DuckDuckGo qui ne nécessite pas de clé API. Vous pouvez utiliser SerpAPI ou Bing API pour de meilleurs résultats.

### 4. Personnaliser la configuration

- **`config/medias.yml`** : Ajoutez/modifiez les médias à analyser
- **`config/keywords.yml`** : Personnalisez les mots-clés féministes et équilibrants
- **`config/search_providers.yml`** : Configurez les providers de recherche

## 📊 Utilisation

### Pipeline complet

**Méthode recommandée (automatique) :**

**Sur Windows :**
```bash
run_pipeline.bat
```

**Sur Linux/Mac :**
```bash
python scripts/run_pipeline.py
```

**Méthode manuelle (étape par étape) :**

```bash
# 1. Collecte des URLs
python scripts/collect_urls.py

# 2. Téléchargement des articles
python scripts/fetch_articles.py

# 3. Parsing des articles
python scripts/parse_articles.py

# 4. Analyse et scoring
python scripts/analyze_articles.py

# 5. Génération des statistiques
python scripts/build_stats.py
```

### Lancement du dashboard

**Sur Windows :**
```bash
start_dashboard.bat
```

**Sur Linux/Mac :**
```bash
python app/api.py
```

Puis ouvrez votre navigateur à l'adresse : `http://localhost:5000`

### Scripts utilitaires

Le projet inclut également plusieurs scripts utilitaires pour la maintenance des données :

- **`scripts/filter_franceculture.py`** : Supprime tous les articles de franceculture.fr des données
- **`scripts/filter_old_articles.py`** : Supprime les articles publiés avant 2000 ou après 2025
- **`scripts/remove_duplicates.py`** : Détecte et supprime les doublons dans tous les fichiers CSV
- **`scripts/statistical_tests.py`** : Effectue des tests statistiques sur les données
- **`scripts/validation_inter_codage.py`** : Outil de validation inter-codage pour la qualité des données

## 🔄 Automatisation

Pour automatiser le pipeline sur votre serveur, créez un script cron ou une tâche planifiée :

**Sur Windows (Tâche planifiée) :**
- Ouvrez le Planificateur de tâches Windows
- Créez une tâche qui exécute `run_pipeline.bat` chaque jour à l'heure souhaitée

**Sur Linux/Mac (Cron) :**
```bash
# Exemple de crontab (exécution chaque nuit à 3h)
0 3 * * * cd /chemin/vers/observatoire_medias && python scripts/run_pipeline.py
```

**Note** : Il est recommandé d'utiliser `run_pipeline.py` plutôt que d'exécuter les scripts individuellement, car il gère automatiquement les erreurs et fournit un résumé détaillé.

## 📈 Métriques calculées

Pour chaque article, l'observatoire calcule :

- **Score féministe** : Nombre d'occurrences des mots-clés féministes
- **Score équilibrant** : Nombre d'occurrences des mots-clés équilibrants (sources neutres, mention des victimes masculines, etc.)
- **Indice militant** : `score_feministe - score_balance`
- **Densité** : Score normalisé par rapport à la longueur du texte

Les statistiques agrégées incluent :

- Indice militant moyen par média
- Nombre d'articles analysés
- Pourcentage d'articles sans mots-clés équilibrants
- Top 10 des articles les plus militants

## ⚖️ Aspects légaux

**Important** : Ce projet respecte les bonnes pratiques de scraping web :

- ✅ Respect des `robots.txt`
- ✅ Limitation des requêtes (délais entre requêtes)
- ✅ Ne republie pas le contenu intégral des articles
- ✅ Affiche uniquement les métadonnées (URL, titre, scores)

**Note** : Assurez-vous de respecter les conditions d'utilisation des sites web et des APIs utilisées.

## 🔬 Validation et Rigueur Méthodologique

Pour garantir la qualité et la rigueur des résultats, plusieurs outils sont disponibles :

### Audit du parsing

Vérifiez régulièrement la qualité de l'extraction du texte :

```bash
python scripts/audit_parsing.py
```

Ce script génère un rapport HTML interactif permettant de comparer manuellement les articles parsés avec les originaux.

### Tests de sensibilité

Testez l'impact des mots-clés sur les résultats :

```bash
python scripts/test_sensitivity.py
```

Ce script analyse :
- La fréquence d'utilisation de chaque mot-clé
- L'impact estimé de la suppression de mots-clés
- Les mots-clés jamais trouvés (candidats à la suppression)

### Documentation méthodologique

Consultez `METHODOLOGIE.md` pour :
- La justification de chaque mot-clé
- Les limites et biais connus
- Les recommandations d'interprétation
- Les améliorations futures prévues

## 🛠️ Développement

### Ajouter un nouveau média

Éditez `config/medias.yml` et ajoutez :

```yaml
- name: "Nom du média"
  domain: "domaine.fr"
```

### Ajouter des mots-clés

Éditez `config/keywords.yml` et ajoutez vos mots-clés dans les sections appropriées.

### Personnaliser le dashboard

Les fichiers frontend sont dans `app/static/` :
- `index.html` : Structure HTML
- `app.js` : Logique JavaScript (Chart.js)
- `style.css` : Styles CSS

## 📝 Notes

- Les données sont stockées localement dans le dossier `data/`
- Le dashboard se met à jour automatiquement toutes les 5 minutes
- Les scripts gèrent automatiquement les doublons et les erreurs
- Utilisez `run_pipeline.bat` (Windows) ou `run_pipeline.py` (Linux/Mac) pour exécuter le pipeline complet en une seule commande
- Le script d'orchestration vous permet de continuer malgré les erreurs et affiche un résumé détaillé à la fin

## 🤝 Contribution

Ce projet est modulaire et peut être étendu facilement :
- Ajout de nouveaux providers de recherche
- Amélioration des parseurs HTML spécifiques par média
- Ajout de nouvelles métriques d'analyse
- Export des données vers MongoDB ou autres bases

## 📄 Licence

Ce projet est fourni à des fins d'analyse et de recherche. Respectez les droits d'auteur et les conditions d'utilisation des sites web analysés.


