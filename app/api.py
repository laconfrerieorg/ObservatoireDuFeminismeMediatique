#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Flask pour servir les statistiques de l'Observatoire des médias.
"""

import os
import json
from pathlib import Path
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
STATS_FILE = DATA_DIR / "stats_daily.json"


@app.route('/')
def index():
    """Serve la page principale du dashboard."""
    return send_from_directory('static', 'index.html')


@app.route('/api/stats')
def get_stats():
    """Retourne les statistiques au format JSON."""
    if not STATS_FILE.exists():
        return jsonify({
            'error': 'Aucune statistique disponible',
            'generated_at': None
        }), 404
    
    try:
        with open(STATS_FILE, 'r', encoding='utf-8') as f:
            stats = json.load(f)
        return jsonify(stats)
    except Exception as e:
        return jsonify({
            'error': f'Erreur lors de la lecture des stats: {str(e)}'
        }), 500


@app.route('/api/medias')
def get_medias():
    """Retourne uniquement les stats par média."""
    if not STATS_FILE.exists():
        return jsonify([]), 404
    
    try:
        with open(STATS_FILE, 'r', encoding='utf-8') as f:
            stats = json.load(f)
        return jsonify(stats.get('medias', []))
    except Exception as e:
        return jsonify({
            'error': f'Erreur: {str(e)}'
        }), 500


@app.route('/api/top-militant')
def get_top_militant():
    """Retourne le top des articles les plus militants."""
    if not STATS_FILE.exists():
        return jsonify([]), 404
    
    try:
        with open(STATS_FILE, 'r', encoding='utf-8') as f:
            stats = json.load(f)
        return jsonify(stats.get('top_militant_articles', []))
    except Exception as e:
        return jsonify({
            'error': f'Erreur: {str(e)}'
        }), 500


@app.route('/api/summary')
def get_summary():
    """Retourne le résumé global."""
    if not STATS_FILE.exists():
        return jsonify({}), 404
    
    try:
        with open(STATS_FILE, 'r', encoding='utf-8') as f:
            stats = json.load(f)
        return jsonify(stats.get('summary', {}))
    except Exception as e:
        return jsonify({
            'error': f'Erreur: {str(e)}'
        }), 500


if __name__ == '__main__':
    # Configuration pour le développement
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    app.run(host='0.0.0.0', port=port, debug=debug)

