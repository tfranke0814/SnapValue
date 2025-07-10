"""
Mock Market Service for development
"""
from typing import Dict, Optional, List
from datetime import datetime
import random

from app.services.base_service import BaseService
from app.utils.logging import get_logger

logger = get_logger(__name__)

class MockMarketService(BaseService):
    """Mock Market Service for development"""
    
    def __init__(self, db=None):
        super().__init__(db)
        logger.info("Initialized MockMarketService for development")
    
    def validate_input(self, data) -> bool:
        """Validate input for market analysis"""
        return isinstance(data, dict)
    
    def process(self, data: Dict) -> Dict:
        """Process market analysis - main entry point"""
        return self.analyze_item_market_value(
            data.get('embeddings'),
            data.get('extracted_features'),
            data.get('category'),
            data.get('market_options', {})
        )
    
    def analyze_item_market_value(
        self,
        embeddings: Optional[Dict] = None,
        extracted_features: Optional[Dict] = None,
        category: Optional[str] = None,
        market_options: Optional[Dict] = None
    ) -> Dict:
        """
        Analyze market value with mock data
        """
        logger.info(f"Performing mock market analysis for category: {category}")
        
        # Generate mock pricing based on category
        base_prices = {
            'electronics': {'min': 100, 'max': 800, 'avg': 450},
            'jewelry': {'min': 50, 'max': 2000, 'avg': 500},
            'collectibles': {'min': 20, 'max': 1500, 'avg': 300},
            'art': {'min': 100, 'max': 5000, 'avg': 1200},
            'furniture': {'min': 50, 'max': 1200, 'avg': 400}
        }
        
        price_range = base_prices.get(category, base_prices['electronics'])
        
        # Add some randomness to make it more realistic
        variance = random.uniform(0.8, 1.2)
        estimated_value = int(price_range['avg'] * variance)
        price_min = max(int(estimated_value * 0.7), price_range['min'])
        price_max = min(int(estimated_value * 1.3), price_range['max'])
        
        return {
            'estimated_value': estimated_value,
            'currency': 'USD',
            'price_range': {
                'min': price_min,
                'max': price_max,
                'currency': 'USD'
            },
            'confidence_score': random.uniform(0.75, 0.95),
            'comparable_items': [
                {
                    'title': f'Similar {category} item 1',
                    'price': estimated_value + random.randint(-50, 50),
                    'condition': 'used',
                    'source': 'mock_marketplace',
                    'similarity_score': 0.85
                },
                {
                    'title': f'Similar {category} item 2', 
                    'price': estimated_value + random.randint(-75, 75),
                    'condition': 'good',
                    'source': 'mock_auction',
                    'similarity_score': 0.78
                }
            ],
            'market_trends': {
                'trend_direction': random.choice(['rising', 'stable', 'declining']),
                'price_change_30d': random.uniform(-0.1, 0.15),
                'volume_change_30d': random.uniform(-0.2, 0.25),
                'demand_level': random.choice(['low', 'medium', 'high'])
            },
            'analysis_metadata': {
                'items_analyzed': random.randint(50, 200),
                'data_sources': ['mock_marketplace', 'mock_auction', 'mock_retail'],
                'analysis_date': datetime.utcnow().isoformat(),
                'market_coverage': 'mock_region'
            }
        }
    
    def search_comparable_items(
        self,
        features: Dict,
        category: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """Search for comparable items - mock implementation"""
        return [
            {
                'title': f'Comparable {category} item {i+1}',
                'price': random.randint(100, 800),
                'condition': random.choice(['new', 'like_new', 'good', 'fair']),
                'source': random.choice(['ebay', 'amazon', 'facebook']),
                'similarity_score': random.uniform(0.6, 0.9),
                'listing_date': datetime.utcnow().isoformat()
            }
            for i in range(min(limit, 5))
        ]
    
    def get_market_trends(self, category: str, timeframe: int = 30) -> Dict:
        """Get market trends - mock implementation"""
        return {
            'category': category,
            'timeframe_days': timeframe,
            'price_trend': random.choice(['up', 'down', 'stable']),
            'average_price_change': random.uniform(-0.1, 0.1),
            'volume_change': random.uniform(-0.2, 0.2),
            'top_brands': ['Apple', 'Samsung', 'Sony'],
            'popular_models': ['Model A', 'Model B', 'Model C']
        }
    
    def health_check(self) -> bool:
        """Health check for mock market service"""
        return True