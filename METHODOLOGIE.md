# 📚 Méthodologie de l'Observatoire des médias

## 🎯 Objectif

Cet observatoire mesure automatiquement la présence du narratif féministe militant dans les médias français en analysant la fréquence de mots-clés spécifiques dans les articles.

## 🔬 Méthode de Scoring

### Principe de double scoring avec pondération

Le système utilise deux scores complémentaires avec un système de pondération pour refléter l'intensité idéologique des termes :

1. **Score féministe** : Compte les occurrences pondérées de mots-clés associés au narratif féministe militant
2. **Score équilibrant** : Compte les occurrences pondérées de mots-clés qui suggèrent un traitement nuancé ou équilibré

### Formules de calcul

#### Score Féministe
```
Score Féministe = Σ (Occurrences × Pondération)
```

Les mots-clés sont organisés en catégories avec des pondérations différentes :
- **Critique système** (poids 3) : Termes directement issus de la théorie du genre et des mouvements radicaux. Exemples : "patriarcat systémique", "culture du viol", "sexisme structurel"
- **Action & Identité** (poids 2) : Termes popularisés par le militantisme mais repris dans le grand public. Exemples : "intersectionnalité", "charge mentale", "mansplaining"
- **Génériques** (poids 1) : Termes féministes mais moins spécifiquement militants. Exemples : "féminisme", "égalité femmes-hommes", "droits des femmes"

**Justification des pondérations** :
- Poids 3 : Termes très spécifiques aux cadres d'analyse militants, rarement utilisés en dehors de ce contexte
- Poids 2 : Concepts diffusés mais qui orientent fortement l'analyse vers une perspective militante
- Poids 1 : Termes génériques qui peuvent apparaître dans divers contextes mais restent associés au mouvement féministe

#### Score Équilibrant
```
Score Équilibrant = Σ (Occurrences × Pondération)
```

Les mots-clés équilibrants ont des pondérations négatives :
- **Neutralité** (poids -3) : Termes qui cherchent activement à contrecarrer l'approche unilatérale. Exemples : "toutes les victimes", "approche nuancée", "présomption d'innocence"
- **Sources statistiques** (poids -2) : Introduction de thèmes moins abordés par le narratif militant. Exemples : "victimes masculines", "suicides masculins", "père isolé"
- **Nuance & Complexité** (poids -1) : Termes suggérant une analyse nuancée. Exemples : "contexte", "multifactoriel", "complexité"
- **Méthodologie** (poids -1) : Termes suggérant une approche rigoureuse. Exemples : "biais", "limites de l'étude", "méthodologie"
- **Diversité** (poids -1) : Mention de situations diverses. Exemples : "couples lesbiens", "diversité"

**Justification des pondérations négatives** :
- Poids -3 : Termes qui signalent explicitement une volonté de dépasser le cadre binaire et d'adopter une approche inclusive
- Poids -2 : Termes qui introduisent des perspectives ou données factuelles souvent absentes du narratif militant classique
- Poids -1 : Termes suggérant une approche nuancée ou méthodologique sans être explicitement contre-narratif

#### Métrique principale : Pourcentage de militantisme

```
pct_militantisme = (score_feministe / longueur_texte) × 1000 × 10
```

Cette métrique mesure **uniquement** l'intensité du militantisme féministe dans l'article, **sans comparaison** avec les mots-clés équilibrants. Elle est basée sur la densité des mots-clés féministes par rapport à la longueur du texte.

**Principe** :
- Le score féministe est normalisé par rapport à la longueur du texte (pour 1000 mots)
- Cette métrique permet de comparer les articles indépendamment de leur longueur
- Les mots-clés équilibrants ne sont **pas** pris en compte dans ce calcul

**Exemple de calcul** :
- Article de 2000 mots avec "patriarcat" (poids 3) et "féminicide" (poids 2)
- Score féministe = 5
- Score pour 1000 mots = (5 / 2000) × 1000 = 2.5
- Pourcentage = 2.5 × 10 = 25%

**Interprétation** :
- **0-10%** : Très peu de mots-clés féministes
- **10-30%** : Présence modérée de mots-clés féministes
- **30-50%** : Présence importante de mots-clés féministes
- **50-70%** : Présence très importante de mots-clés féministes
- **70-100%** : Présence extrêmement élevée de mots-clés féministes

**Note** : Cette métrique ne tient pas compte des mots-clés équilibrants. Pour une analyse complète, consultez également l'`indice_militant` qui compare les deux types de mots-clés.

## 📝 Justification des Mots-Clés

### Structure des mots-clés

Les mots-clés sont organisés en catégories thématiques avec des pondérations reflétant leur intensité idéologique. Cette structure permet un scoring plus nuancé et précis.

### Mots-clés féministes (`feminist_keywords`)

#### 1. Critique Système (Pondération : 3 points)

**Justification** : Ces termes sont directement issus de la théorie du genre et des mouvements radicaux/intersectionnels. Leur présence est un marqueur fort d'un cadre d'analyse militant.

**Exemples** :
- "patriarcat", "patriarcat systémique" : Concept central du féminisme radical, suggère une analyse systémique
- "culture du viol" : Expression militante spécifique
- "masculinité toxique" : Concept militant issu des études de genre
- "domination masculine" : Terme du féminisme radical
- "inégalités structurelles" : Cadre d'analyse systémique
- "sexisme intériorisé" : Concept théorique militant

**Origine** : Théorie du genre, féminisme radical, études intersectionnelles

#### 2. Action & Identité (Pondération : 2 points)

**Justification** : Termes popularisés par le militantisme mais qui peuvent être repris dans des articles grand public. Indique un alignement modéré avec le narratif militant.

**Exemples** :
- "féminicide", "féminicides" : Terme militant créé pour désigner spécifiquement les meurtres de femmes
- "violences faites aux femmes" : Formulation militante (vs "violences conjugales" plus neutre)
- "violence obstétricale" : Concept militant spécifique
- "charge mentale" : Concept popularisé par le militantisme
- "plafond de verre" : Expression militante
- "victim blaming" : Terme militant
- "violence économique" : Concept militant
- "travail gratuit" (des femmes) : Expression militante

**Origine** : Mouvements féministes militants français, collectifs, associations

#### 3. Génériques (Pondération : 1 point)

**Justification** : Termes féministes mais moins spécifiquement militants. Peuvent apparaître dans des contextes variés.

**Exemples** :
- "féminisme", "féministe", "féministes" : Termes génériques
- "violences conjugales" : Terme neutre mais souvent utilisé dans un contexte militant
- "sexisme", "misogynie" : Termes descriptifs mais associés au militantisme
- "inégalités femmes-hommes" : Expression courante mais associée au féminisme

**Origine** : Vocabulaire courant mais associé au mouvement féministe

### Mots-clés équilibrants (`balanced_keywords`)

Ces mots-clés ont des pondérations négatives car ils réduisent le score militant en indiquant un traitement nuancé ou équilibré.

#### 1. Neutralité (Pondération : -2 points)

**Justification** : Termes qui signalent une volonté de dépasser le cadre binaire "victime=femme / agresseur=homme". Réduction forte du score militant.

**Exemples** :
- "hommes victimes", "violences faites aux hommes" : Mention explicite des hommes comme victimes
- "victimes masculines", "hommes battus" : Reconnaissance des hommes victimes
- "violence réciproque", "violences réciproques" : Reconnaissance que les violences peuvent être bidirectionnelles
- "toutes les victimes" : Approche inclusive
- "point de vue opposé", "approche nuancée" : Indication de nuance
- "sources multiples" : Diversité des sources

**Origine** : Termes suggérant un traitement équilibré et inclusif

#### 2. Nuance & Complexité (Pondération : -1 point)

**Justification** : Indique une prise en compte de la complexité des situations. Réduction modérée du score militant.

**Exemples** :
- "nuance", "nuances", "contexte", "complexité" : Termes suggérant une analyse nuancée
- "multifactoriel", "facteurs multiples" : Reconnaissance de la complexité
- "facteurs de risque", "facteurs sociaux" : Approche analytique
- "diversité", "variété des situations" : Reconnaissance de la diversité

**Origine** : Vocabulaire analytique suggérant une approche nuancée

#### 3. Méthodologie (Pondération : -1 point)

**Justification** : Suggère une approche rigoureuse et critique. Réduction modérée du score militant.

**Exemples** :
- "biais", "limites de l'étude", "limitations" : Mention des limites méthodologiques
- "échantillon représentatif", "représentatif" : Approche méthodologique rigoureuse
- "méthodologie" : Indication d'une approche scientifique

**Origine** : Vocabulaire méthodologique suggérant une approche critique

#### 4. Diversité (Pondération : -1 point)

**Justification** : Mention de situations diverses. Réduction modérée du score militant.

**Exemples** :
- "couples lesbiens", "couples de même sexe" : Diversité des situations

**⚠️ Exclusion importante** : Les noms d'institutions (INSEE, INED, etc.) ou termes génériques ("statistiques", "données", "chercheurs") ne sont PAS des indicateurs d'équilibre car ils peuvent être utilisés pour appuyer n'importe quel narratif, y compris militant.

## ⚖️ Justification des Pondérations

### Pourquoi ces valeurs spécifiques ?

Les pondérations ont été choisies pour refléter l'intensité idéologique et la spécificité des termes :

#### Pondérations féministes (1, 2, 3)

**Poids 3 - Critique système** :
- **Justification** : Ces termes sont très spécifiques aux cadres d'analyse militants et rarement utilisés en dehors de ce contexte
- **Exemple** : "patriarcat systémique" est un terme technique issu de la théorie du genre, presque exclusivement utilisé dans un contexte militant ou académique militant
- **Pourquoi pas 4 ou 5 ?** : Un poids trop élevé créerait une distorsion excessive. Un poids de 3 permet de distinguer ces termes sans créer un écart trop important avec les autres catégories

**Poids 2 - Action & Identité** :
- **Justification** : Ces termes sont popularisés par le militantisme mais peuvent être repris dans des articles grand public
- **Exemple** : "charge mentale" est un concept militant mais qui est maintenant utilisé dans des contextes variés
- **Pourquoi pas 1 ou 3 ?** : Un poids de 2 reflète leur caractère intermédiaire : plus militants que les termes génériques, mais moins spécifiques que les termes de critique systémique

**Poids 1 - Génériques** :
- **Justification** : Ces termes peuvent apparaître dans divers contextes mais restent associés au mouvement féministe
- **Exemple** : "féminisme" peut être mentionné de manière neutre ou même critique
- **Pourquoi pas 0.5 ou 2 ?** : Un poids de 1 permet de comptabiliser ces termes sans leur donner trop d'importance, tout en reconnaissant leur association avec le mouvement

#### Pondérations équilibrantes (-1, -2, -3)

**Poids -3 - Neutralité** :
- **Justification** : Ces termes cherchent activement à contrecarrer l'approche unilatérale et signalent explicitement une volonté de dépasser le cadre binaire
- **Exemple** : "toutes les victimes" ou "présomption d'innocence" sont des formulations qui vont explicitement à l'encontre d'un narratif unilatéral
- **Pourquoi pas -4 ou -5 ?** : Un poids trop négatif pourrait créer une surcompensation. Un poids de -3 est suffisant pour signaler fortement l'équilibre sans distorsion excessive

**Poids -2 - Sources statistiques** :
- **Justification** : Ces termes introduisent des perspectives ou données factuelles souvent absentes du narratif militant classique
- **Exemple** : "victimes masculines" ou "suicides masculins" introduisent des thèmes rarement abordés par le narratif militant
- **Pourquoi pas -1 ou -3 ?** : Un poids de -2 reflète leur importance modérée : ils introduisent une perspective alternative sans être aussi explicites que les termes de neutralité

**Poids -1 - Nuance, Méthodologie, Diversité** :
- **Justification** : Ces termes suggèrent une approche nuancée ou méthodologique sans être explicitement contre-narratif
- **Exemple** : "contexte" ou "biais" suggèrent une approche analytique sans être explicitement contre le narratif militant
- **Pourquoi pas -0.5 ou -2 ?** : Un poids de -1 permet de reconnaître ces nuances sans leur donner trop d'importance

### Échelle de pondération

L'échelle choisie (1-3 pour féministes, -1 à -3 pour équilibrants) permet :
- ✅ Une distinction claire entre les niveaux d'intensité
- ✅ Un équilibre entre les deux types de scores
- ✅ Une interprétation intuitive des résultats
- ✅ Une flexibilité pour ajuster les pondérations si nécessaire

**Note méthodologique** : Ces pondérations sont le résultat d'une analyse qualitative des termes et peuvent être ajustées en fonction des résultats empiriques et des tests de sensibilité.

## 🔍 Validation et Robustesse

### Tests de sensibilité

Pour tester la robustesse du modèle :

1. **Variation des mots-clés** : Retirer ou ajouter quelques mots-clés et observer l'impact sur les scores
2. **Seuil minimum** : Tester différents seuils de longueur de texte minimum
3. **Pondération** : Tester différentes pondérations pour les mots-clés "forts"

### Audit du parsing

Le parsing est l'étape la plus fragile. Un audit régulier est nécessaire :

1. **Échantillonnage aléatoire** : Prendre 10-20 articles parsés
2. **Vérification manuelle** : Comparer le texte extrait avec l'article original
3. **Taux d'erreur** : Calculer le pourcentage d'articles mal parsés

Voir le script `scripts/audit_parsing.py` pour automatiser cet audit.

## ⚖️ Limites et Biais

### Limites connues

1. **Pas d'analyse contextuelle** : Le système compte les occurrences sans analyser le contexte. Un article qui critique le féminisme sera quand même compté comme "féministe" s'il mentionne les termes. Par exemple, "le patriarcat n'existe pas" comptera quand même comme une occurrence de "patriarcat".

2. **Pondération fixe** : Les pondérations sont fixes et ne s'adaptent pas au contexte. Un terme peut avoir un poids différent selon le contexte (par exemple, "féminisme" dans un article critique vs un article promotionnel).

3. **Dépendance au parsing** : La qualité des résultats dépend de la qualité de l'extraction du texte. Si le parsing échoue, l'article ne sera pas analysé correctement.

4. **Biais de sélection** : Les articles sont collectés via recherche par mots-clés, ce qui peut créer un biais vers les articles déjà militants.

### Biais potentiels

- **Biais de confirmation** : Les mots-clés peuvent être choisis pour confirmer une hypothèse préexistante
- **Biais linguistique** : Certains médias peuvent utiliser un vocabulaire différent sans être moins militants
- **Biais temporel** : Les termes militants évoluent dans le temps

## 📊 Interprétation des Résultats

### Ce que mesure l'observatoire

✅ **Mesure** : La fréquence de certains termes dans les articles  
✅ **Compare** : Les médias entre eux sur cette métrique  
✅ **Identifie** : Les tendances temporelles

### Ce que l'observatoire NE mesure PAS

❌ **Ne mesure PAS** : La qualité journalistique  
❌ **Ne mesure PAS** : L'objectivité globale  
❌ **Ne mesure PAS** : L'impact sur les lecteurs  
❌ **Ne mesure PAS** : La véracité des informations

### Recommandations d'interprétation

1. **Utiliser comme indicateur, pas comme preuve** : Les scores sont des indicateurs, pas des preuves absolues
2. **Considérer le contexte** : Un score élevé peut être justifié dans certains contextes
3. **Comparer avec d'autres métriques** : Ne pas se fier uniquement à cet observatoire
4. **Examiner les articles individuels** : Regarder les articles les plus militants pour comprendre pourquoi

## 🔄 Améliorations Futures

### Court terme

- [ ] Audit régulier du parsing
- [ ] Tests de sensibilité des mots-clés
- [ ] Documentation des cas limites

### Moyen terme

- [x] Pondération des mots-clés selon leur "force" idéologique ✅ **Implémenté**
- [ ] Analyse contextuelle basique (détection de négation)
- [ ] Validation manuelle d'un échantillon d'articles
- [ ] Ajustement des pondérations basé sur les résultats empiriques

### Long terme

- [ ] Modèles NLP pour l'analyse contextuelle
- [ ] Classification automatique des articles par type (reportage, éditorial, etc.)
- [ ] Analyse de sentiment pour distinguer critique et promotion

## 📚 Références

- Méthodologie inspirée des travaux sur l'analyse de contenu automatisée
- Adaptation des techniques de "keyword frequency analysis"
- Références aux travaux sur le biais médiatique et l'analyse de discours

---

**Dernière mise à jour** : 2025-01-XX  
**Version** : 1.0

