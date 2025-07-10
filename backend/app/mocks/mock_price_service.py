"""
Mock Price Service for development
"""
from typing import Dict, Optional, List
from datetime import datetime
import random

from app.services.base_service import BaseService
from app.utils.logging import get_logger

logger = get_logger(__name__)

class MockPriceService(BaseService):
    """Mock Price Service for development"""
    
    def __init__(self, db=None):
        super().__init__(db)
        logger.info("Initialized MockPriceService for development")
    
    def validate_input(self, data) -> bool:
        """Validate input for price calculation"""
        return isinstance(data, dict)
    
    def process(self, data: Dict) -> Dict:
        """Process price calculation - main entry point"""
        return self.calculate_price_estimate(
            data.get('ai_analysis'),
            data.get('market_data'),
            data.get('item_condition'),
            data.get('options', {})
        )
    
    def calculate_price_estimate(
        self,
        ai_analysis: Optional[Dict] = None,
        market_data: Optional[Dict] = None,
        item_condition: Optional[str] = None,
        options: Optional[Dict] = None
    ) -> Dict:
        """
        Calculate price estimate with mock logic
        """
        logger.info("Performing mock price calculation")
        
        # Base price from market data or default
        if market_data and 'estimated_value' in market_data:
            base_price = market_data['estimated_value']
        else:
            base_price = random.randint(100, 500)
        
        # Condition adjustments
        condition_multipliers = {
            'new': 1.0,
            'like_new': 0.85,
            'excellent': 0.75,
            'good': 0.60,
            'fair': 0.40,
            'poor': 0.20
        }
        
        condition = item_condition or 'good'
        condition_multiplier = condition_multipliers.get(condition.lower(), 0.60)
        
        # AI confidence adjustment
        ai_confidence = 0.85
        if ai_analysis and 'confidence_score' in ai_analysis:
            ai_confidence = ai_analysis['confidence_score']
        
        # Calculate final estimate
        estimated_price = int(base_price * condition_multiplier)
        confidence = min(ai_confidence * 0.9, 0.95)
        
        # Price range based on confidence
        uncertainty = 1 - confidence
        range_factor = 0.2 + (uncertainty * 0.3)  # 20-50% range based on confidence
        
        price_min = int(estimated_price * (1 - range_factor))
        price_max = int(estimated_price * (1 + range_factor))
        
        return {
            'estimated_price': estimated_price,
            'currency': 'USD',
            'price_range': {
                'min': price_min,
                'max': price_max,
                'currency': 'USD'
            },
            'confidence_score': confidence,
            'factors_considered': {
                'ai_analysis_confidence': ai_confidence,
                'condition_adjustment': condition_multiplier,
                'market_data_quality': random.uniform(0.7, 0.9),
                'comparable_items_count': random.randint(5, 20)
            },
            'pricing_breakdown': {
                'base_market_value': base_price,
                'condition_adjusted': estimated_price,
                'final_estimate': estimated_price
            },
            'calculation_metadata': {
                'method': 'mock_ai_market_hybrid',
                'version': '1.0',
                'calculated_at': datetime.utcnow().isoformat(),
                'factors_used': ['ai_analysis', 'market_data', 'condition']
            }
        }
    
    def get_price_history(self, item_features: Dict, days: int = 30) -> List[Dict]:
        """Get price history - mock implementation"""
        return [
            {
                'date': datetime.utcnow().isoformat(),
                'price': random.randint(100, 600),
                'source': 'mock_market',
                'condition': random.choice(['new', 'used', 'refurbished'])
            }
            for _ in range(min(days // 5, 10))  # Sample data points
        ]
    
    def compare_prices(self, item_features: Dict, sources: List[str] = None) -> Dict:
        """Compare prices across sources - mock implementation"""
        sources = sources or ['ebay', 'amazon', 'facebook_marketplace']
        
        return {
            'comparisons': [
                {
                    'source': source,
                    'average_price': random.randint(150, 500),
                    'price_range': {
                        'min': random.randint(100, 200),
                        'max': random.randint(400, 600)
                    },
                    'listing_count': random.randint(5, 50),
                    'confidence': random.uniform(0.6, 0.9)
                }
                for source in sources
            ],
            'recommended_price': random.randint(200, 400),
            'analysis_date': datetime.utcnow().isoformat()
        }
    
    def health_check(self) -> bool:
        """Health check for mock price service"""
        return True