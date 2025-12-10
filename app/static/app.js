// Configuration
const API_BASE_URL = window.location.origin;

// Éléments DOM
const lastUpdateEl = document.getElementById('lastUpdate');
const totalArticlesEl = document.getElementById('totalArticles');
const avgMilitantEl = document.getElementById('avgMilitant');
const pctWithoutBalanceEl = document.getElementById('pctWithoutBalance');
const totalMediasEl = document.getElementById('totalMedias');
const topArticlesBody = document.getElementById('topArticlesBody');
const mediasDetailsBody = document.getElementById('mediasDetailsBody');

// Charts
let mediasChart = null;
let articlesChart = null;
let timeChart = null;

// Fonction principale de chargement
async function loadData() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/stats`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        const data = await response.json();
        
        updateSummary(data);
        updateCharts(data);
        updateTimeChart(data.by_period || []);
        updateTopArticles(data.top_militant_articles || []);
        updateMediasDetails(data.medias || []);
        updateAllArticles(data.all_articles_by_media || []);
        updateLastUpdate(data.generated_at);
    } catch (error) {
        console.error('Erreur lors du chargement des données:', error);
        showError('Erreur lors du chargement des données. Vérifiez que les statistiques ont été générées.');
    }
}

// Mise à jour du résumé
function updateSummary(data) {
    const summary = data.summary || {};
    
    totalArticlesEl.textContent = data.total_articles || 0;
    // Afficher le nombre total de mots-clés féministes
    avgMilitantEl.textContent = summary.total_mots_cles_feministes_global || 0;
    // Cacher ou masquer l'élément "sans équilibrants" qui n'a plus de sens
    if (pctWithoutBalanceEl) {
        pctWithoutBalanceEl.parentElement.style.display = 'none';
    }
    totalMediasEl.textContent = summary.n_medias || 0;
}

// Mise à jour de la date de dernière mise à jour
function updateLastUpdate(dateStr) {
    if (!dateStr) {
        lastUpdateEl.textContent = 'Date inconnue';
        return;
    }
    
    try {
        const date = new Date(dateStr);
        const formatted = date.toLocaleString('fr-FR', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
        lastUpdateEl.textContent = `Dernière mise à jour: ${formatted}`;
    } catch (e) {
        lastUpdateEl.textContent = `Dernière mise à jour: ${dateStr}`;
    }
}

// Mise à jour des graphiques
function updateCharts(data) {
    const medias = data.medias || [];
    
    // Trier par score ajusté (décroissant)
    // Le score ajusté combine le pourcentage de militantisme avec un facteur de confiance
    // basé sur le nombre d'articles pour tenir compte de la représentativité de l'échantillon
    const sortedMedias = [...medias].sort((a, b) => 
        (b.score_ajuste || 0) - (a.score_ajuste || 0)
    );
    
    const labels = sortedMedias.map(m => m.domain);
    const pctMilitantisme = sortedMedias.map(m => m.pct_militantisme_moyen || 0);
    const scoreAjuste = sortedMedias.map(m => m.score_ajuste || 0);
    const articles = sortedMedias.map(m => m.n_articles);
    const facteurConfiance = sortedMedias.map(m => m.facteur_confiance || 0);
    
    // Graphique du pourcentage de militantisme moyen par média
    // Cette métrique reflète mieux l'intensité du féminisme car elle normalise par rapport à la longueur du texte
    const mediasCtx = document.getElementById('mediasChart').getContext('2d');
    if (mediasChart) {
        mediasChart.destroy();
    }
    
    mediasChart = new Chart(mediasCtx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Pourcentage de militantisme moyen (%)',
                data: pctMilitantisme,
                backgroundColor: 'rgba(231, 76, 60, 0.7)',  // Rouge pour le militantisme
                borderColor: 'rgba(231, 76, 60, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const media = sortedMedias[context.dataIndex];
                            const scoreAjuste = context.parsed.y.toFixed(2);
                            const pctMilitant = (media.pct_militantisme_moyen || 0).toFixed(1);
                            const confiance = ((media.facteur_confiance || 0) * 100).toFixed(1);
                            const moyenneMotsCles = (media.moyenne_mots_cles_feministes || 0).toFixed(2);
                            return [
                                `Score ajusté: ${scoreAjuste}`,
                                `Pourcentage militantisme: ${pctMilitant}%`,
                                `Facteur de confiance: ${confiance}% (${media.n_articles} articles)`,
                                `Moyenne mots-clés/article: ${moyenneMotsCles}`
                            ];
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Score ajusté (militantisme × confiance)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Média'
                    }
                }
            }
        }
    });
    
    // Graphique du nombre d'articles
    const articlesCtx = document.getElementById('articlesChart').getContext('2d');
    if (articlesChart) {
        articlesChart.destroy();
    }
    
    articlesChart = new Chart(articlesCtx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Nombre d\'articles',
                data: articles,
                backgroundColor: 'rgba(102, 126, 234, 0.7)',
                borderColor: 'rgba(102, 126, 234, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.parsed.y} articles`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    },
                    title: {
                        display: true,
                        text: 'Nombre d\'articles'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Média'
                    }
                }
            }
        }
    });
}

// Mise à jour du graphique temporel
function updateTimeChart(periodStats) {
    const timeCtx = document.getElementById('timeChart');
    if (!timeCtx) {
        return;
    }
    
    if (!periodStats || periodStats.length === 0) {
        // Masquer le conteneur si pas de données
        const timeChartContainer = document.querySelector('#timeChart')?.closest('.chart-container');
        if (timeChartContainer) {
            timeChartContainer.style.display = 'none';
        }
        return;
    }
    
    // Trier par année (croissant)
    const sortedPeriods = [...periodStats].sort((a, b) => {
        const yearA = a.year || parseInt(a.period) || 0;
        const yearB = b.year || parseInt(b.period) || 0;
        return yearA - yearB;
    });
    
    const labels = sortedPeriods.map(p => {
        // Formater l'année (ex: "2024" -> "2024")
        const year = p.year || p.period;
        return String(year);
    });
    
    const moyenneMotsCles = sortedPeriods.map(p => p.moyenne_mots_cles_feministes || p.indice_militant_moyen || 0);
    const pctMilitantisme = sortedPeriods.map(p => p.pct_militantisme_moyen || 0);
    const nArticles = sortedPeriods.map(p => p.n_articles || 0);
    
    // Détruire le graphique existant
    if (timeChart) {
        timeChart.destroy();
    }
    
    timeChart = new Chart(timeCtx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Moyenne de mots-clés féministes par article',
                    data: moyenneMotsCles,
                    borderColor: 'rgba(231, 76, 60, 1)',
                    backgroundColor: 'rgba(231, 76, 60, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    yAxisID: 'y'
                },
                {
                    label: 'Pourcentage de militantisme moyen',
                    data: pctMilitantisme,
                    borderColor: 'rgba(102, 126, 234, 1)',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            aspectRatio: 2.5,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        font: {
                            size: 14
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        afterLabel: function(context) {
                            const index = context.dataIndex;
                            return `Articles: ${nArticles[index]}`;
                        }
                    },
                    titleFont: {
                        size: 14
                    },
                    bodyFont: {
                        size: 13
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Année',
                        font: {
                            size: 14,
                            weight: 'bold'
                        }
                    },
                    ticks: {
                        font: {
                            size: 12
                        }
                    }
                },
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Mots-clés féministes (moyenne)',
                        font: {
                            size: 14,
                            weight: 'bold'
                        }
                    },
                    beginAtZero: true,
                    ticks: {
                        font: {
                            size: 12
                        }
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Pourcentage de militantisme (%)',
                        font: {
                            size: 14,
                            weight: 'bold'
                        }
                    },
                    beginAtZero: true,
                    grid: {
                        drawOnChartArea: false
                    },
                    ticks: {
                        font: {
                            size: 12
                        }
                    }
                }
            }
        }
    });
}

// Mise à jour du tableau des statistiques détaillées par média
function updateMediasDetails(medias) {
    if (!medias || medias.length === 0) {
        mediasDetailsBody.innerHTML = '<tr><td colspan="5">Aucune donnée disponible</td></tr>';
        return;
    }
    
    // Trier par score ajusté (décroissant)
    const sortedMedias = [...medias].sort((a, b) => 
        (b.score_ajuste || 0) - (a.score_ajuste || 0)
    );
    
    mediasDetailsBody.innerHTML = sortedMedias.map(media => {
        const scoreAjuste = (media.score_ajuste || 0).toFixed(2);
        const pctMilitant = (media.pct_militantisme_moyen || 0).toFixed(1);
        const confiance = ((media.facteur_confiance || 0) * 100).toFixed(1);
        const medianePct = (media.pct_militantisme_mediane || 0).toFixed(1);
        const ecartTypePct = (media.pct_militantisme_ecart_type || 0).toFixed(1);
        const nArticles = media.n_articles || 0;
        
        return `
            <tr>
                <td>${escapeHtml(media.domain || '')}</td>
                <td>${nArticles}</td>
                <td>${scoreAjuste}</td>
                <td>${pctMilitant}%</td>
                <td>${confiance}%</td>
                <td>${medianePct}%</td>
                <td>${ecartTypePct}%</td>
            </tr>
        `;
    }).join('');
}

// Mise à jour de la liste de tous les articles
function updateAllArticles(articlesByMedia) {
    const container = document.getElementById('allArticlesContainer');
    
    if (!articlesByMedia || articlesByMedia.length === 0) {
        container.innerHTML = '<div class="no-data">⚠️ Aucun article disponible. Veuillez régénérer les statistiques avec: <code>python scripts/build_stats.py</code></div>';
        return;
    }
    
    let html = '';
    
    for (const mediaGroup of articlesByMedia) {
        const domain = mediaGroup.domain || 'unknown';
        const articles = mediaGroup.articles || [];
        const nArticles = mediaGroup.n_articles || 0;
        
        html += `
            <div class="media-group">
                <h3 class="media-group-title">
                    ${escapeHtml(domain)} 
                    <span class="article-count">(${nArticles} article${nArticles > 1 ? 's' : ''})</span>
                </h3>
                <div class="articles-list">
        `;
        
        if (articles.length === 0) {
            html += '<p class="no-articles">Aucun article pour ce média</p>';
        } else {
            html += '<ul class="articles-ul">';
            for (const article of articles) {
                const title = article.title || 'Sans titre';
                const url = article.url || '#';
                const score = article.score_feministe || 0;
                const pct = article.pct_militantisme || 0;
                const datePub = article.date_pub || '';
                
                // Formater la date
                let formattedDate = '';
                if (datePub) {
                    try {
                        const date = new Date(datePub);
                        formattedDate = date.toLocaleDateString('fr-FR', {
                            year: 'numeric',
                            month: 'short',
                            day: 'numeric'
                        });
                    } catch (e) {
                        formattedDate = datePub.substring(0, 10); // Prendre les 10 premiers caractères si format invalide
                    }
                }
                
                html += `
                    <li class="article-item">
                        <div class="article-main">
                            <a href="${escapeHtml(url)}" target="_blank" rel="noopener" class="article-link">
                                ${escapeHtml(title)}
                            </a>
                            ${formattedDate ? `<span class="article-date">${formattedDate}</span>` : ''}
                        </div>
                        <span class="article-meta">
                            <span class="score-badge">${score} mots-clés</span>
                            ${pct > 0 ? `<span class="pct-badge">${pct.toFixed(1)}%</span>` : ''}
                        </span>
                    </li>
                `;
            }
            html += '</ul>';
        }
        
        html += `
                </div>
            </div>
        `;
    }
    
    container.innerHTML = html;
}

// Mise à jour du tableau des top articles
function updateTopArticles(articles) {
    if (!articles || articles.length === 0) {
        topArticlesBody.innerHTML = '<tr><td colspan="6">Aucun article disponible</td></tr>';
        return;
    }
    
    // Trier par nombre de mots-clés féministes (score_feministe)
    const sortedArticles = [...articles].sort((a, b) => 
        (b.score_feministe || 0) - (a.score_feministe || 0)
    );
    
    topArticlesBody.innerHTML = sortedArticles.map((article, index) => {
        const scoreFeministe = article.score_feministe || 0;
        const datePub = article.date_pub || '';
        
        // Formater la date
        let formattedDate = '';
        if (datePub) {
            try {
                const date = new Date(datePub);
                formattedDate = date.toLocaleDateString('fr-FR', {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric'
                });
            } catch (e) {
                formattedDate = datePub.substring(0, 10);
            }
        }
        
        return `
            <tr>
                <td class="rank">${index + 1}</td>
                <td>${escapeHtml(article.title || 'Sans titre')}</td>
                <td>${escapeHtml(article.domain || '')}</td>
                <td>${formattedDate || '-'}</td>
                <td class="indice-positive">${scoreFeministe}</td>
                <td><a href="${escapeHtml(article.url)}" target="_blank" rel="noopener">Lire →</a></td>
            </tr>
        `;
    }).join('');
}

// Fonction d'échappement HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Affichage d'erreur
function showError(message) {
    const container = document.querySelector('.container');
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.style.cssText = `
        background: #e74c3c;
        color: white;
        padding: 20px;
        border-radius: 8px;
        margin: 20px 0;
        text-align: center;
    `;
    errorDiv.textContent = message;
    container.insertBefore(errorDiv, container.firstChild);
}

// Chargement initial
document.addEventListener('DOMContentLoaded', () => {
    loadData();
    
    // Recharger toutes les 5 minutes
    setInterval(loadData, 5 * 60 * 1000);
});

