from flask import Blueprint, jsonify, request, session
from flask_mysqldb import MySQL
from models.product_tracking import ProductTracker
from scraping.serp_scraper import SERPScraper
from datetime import datetime, timedelta
import os

product_research = Blueprint('product_research', __name__)
mysql = MySQL()
api_key = os.environ.get('SERP_API_KEY')

@product_research.route('/api/track-product', methods=['POST'])
def track_product():
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401

    try:
        data = request.json
        product_url = data.get('url')
        target_price = data.get('target_price')
        name = data.get('name')

        if not all([product_url, target_price, name]):
            return jsonify({'error': 'Missing required fields'}), 400

        tracker = ProductTracker(mysql)
        success = tracker.add_product(
            user_id=session['user_id'],
            product_url=product_url,
            target_price=float(target_price),
            name=name
        )

        if success:
            return jsonify({'message': 'Product added to tracking successfully'})
        return jsonify({'error': 'Failed to add product'}), 500
    except Exception as e:
        return jsonify({'error': f'Failed to add product: {str(e)}'}), 500

@product_research.route('/api/price-history/<int:product_id>')
def get_price_history(product_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401

    try:
        tracker = ProductTracker(mysql)
        history = tracker.get_price_history(product_id)
        
        return jsonify({
            'history': [
                {
                    'price': float(h.price),
                    'date': h.date.strftime('%Y-%m-%d %H:%M:%S'),
                    'store': h.store
                }
                for h in history
            ]
        })
    except Exception as e:
        return jsonify({'error': f'Failed to fetch price history: {str(e)}'}), 500

@product_research.route('/api/competitor-analysis/<int:product_id>')
def get_competitor_analysis(product_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401

    try:
        tracker = ProductTracker(mysql)
        competitors = tracker.get_competitor_products(product_id)
        
        return jsonify({
            'competitors': [
                {
                    'url': c.url,
                    'price': float(c.price),
                    'store': c.store,
                    'last_updated': c.last_updated.strftime('%Y-%m-%d %H:%M:%S'),
                    'availability': c.availability
                }
                for c in competitors
            ]
        })
    except Exception as e:
        return jsonify({'error': f'Failed to fetch competitor analysis: {str(e)}'}), 500

@product_research.route('/api/similar-products', methods=['POST'])
def find_similar_products():
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401

    try:
        data = request.json
        product_name = data.get('product_name')
        if not product_name:
            return jsonify({'error': 'Product name is required'}), 400
            
        price_range = data.get('price_range', '')
        
        serp_scraper = SERPScraper(api_key)
        results = serp_scraper.get_shopping_results(
            product_name, 
            price_range=price_range
        )
        
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': f'Failed to fetch similar products: {str(e)}'}), 500
