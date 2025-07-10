from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import json
import hashlib

from app.services.base_service import BaseService
from app.services.market_service import MarketService
from app.utils.price_calculation import PriceCalculator, PriceAnalysis
from app.utils.exceptions import ValidationError, AIProcessingError
from app.utils.logging import get_logger, log_service_call, log_service_result
from app.core.registry import registry
from app.core.config import settings

logger = get_logger(__name__)

class PriceService(BaseService):
    """Service for price estimation and caching"""
    
    def __init__(self, db: Optional[Session] = None):
        super().__init__(db)
        self.market_service = MarketService(db)
        self.price_calculator = PriceCalculator()
        
        # Caching configuration
        self.cache_ttl = settings.CACHE_TTL  # From config
        self.cache = {}  # In-memory cache (Redis would be better for production)
        self.cache_timestamps = {}
    
    def validate_input(self, data) -> bool:
        """Validate input for price estimation"""
        if not isinstance(data, dict):
            return False
        
        # Must have either embeddings or features
        return 'embeddings' in data or 'features' in data
    
    def process(self, data: Dict) -> Dict:
        """Process price estimation - main entry point"""
        if not self.validate_input(data):
            raise ValidationError("Invalid input data for price estimation")
        
        return self.estimate_price(
            data.get('embeddings', {}),
            data.get('features', {}),
            data.get('category'),
            data.get('options', {})
        )
    
    def estimate_price(
        self,
        embeddings: Dict,
        features: Dict,
        category: Optional[str] = None,
        options: Optional[Dict] = None
    ) -> Dict:
        """
        Estimate price for an item with caching
        
        Args:
            embeddings: Item embeddings
            features: Item features
            category: Item category
            options: Estimation options
            
        Returns:
            Dictionary with price estimation and analysis
        """
        if options is None:
            options = {}
        
        log_service_call("PriceService", "estimate_price", 
                        category=category, use_cache=options.get('use_cache', True))
        
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(embeddings, features, category, options)
            
            # Check cache first
            if options.get('use_cache', True):
                cached_result = self._get_cached_result(cache_key)
                if cached_result:
                    log_service_result("PriceService", "estimate_price", True, 
                                     source="cache", estimated_value=cached_result.get('estimated_value'))
                    return cached_result
            
            # Perform market analysis
            market_analysis = self.market_service.analyze_item_market_value(
                embeddings, features, category, options
            )
            
            # Create price estimation result
            result = {
                'estimated_value': market_analysis['estimated_value'],
                'currency': market_analysis['currency'],
                'confidence_score': market_analysis['confidence_score'],
                'price_range': market_analysis['price_range'],
                'market_analysis': market_analysis['market_analysis'],
                'comparable_items': market_analysis['comparable_items'],
                'recommendations': market_analysis['recommendations'],
                'estimation_metadata': {
                    'estimated_at': datetime.utcnow().isoformat(),
                    'method': 'market_comparison',
                    'data_sources': ['market_data', 'similarity_search'],
                    'cache_key': cache_key
                }
            }
            
            # Cache the result
            if options.get('use_cache', True):
                self._cache_result(cache_key, result)
            
            log_service_result("PriceService", "estimate_price", True, 
                             source="computed", estimated_value=result['estimated_value'])
            
            return result
            
        except Exception as e:
            self.log_error(e, "estimate_price")
            raise
    
    def get_price_history(self, item_id: str, days: int = 90) -> Dict:
        """Get price history for an item"""
        log_service_call("PriceService", "get_price_history", 
                        item_id=item_id, days=days)
        
        try:
            # In a real implementation, you'd query historical price data
            # For now, return mock data
            history = self._generate_mock_price_history(item_id, days)
            
            # Analyze trends
            trends = self._analyze_price_history_trends(history)
            
            result = {
                'item_id': item_id,
                'price_history': history,
                'trends': trends,
                'period_days': days,
                'generated_at': datetime.utcnow().isoformat()
            }
            
            log_service_result("PriceService", "get_price_history", True, 
                             data_points=len(history))
            
            return result
            
        except Exception as e:
            self.log_error(e, "get_price_history")
            raise AIProcessingError(f"Price history retrieval failed: {str(e)}")
    
    def compare_prices(
        self,
        item_data_list: List[Dict],
        comparison_type: str = 'market_value'
    ) -> Dict:
        """Compare prices for multiple items"""
        log_service_call("PriceService", "compare_prices", 
                        items_count=len(item_data_list), comparison_type=comparison_type)
        
        try:
            comparisons = []
            
            for i, item_data in enumerate(item_data_list):
                try:
                    # Estimate price for each item
                    price_estimate = self.estimate_price(
                        item_data.get('embeddings', {}),
                        item_data.get('features', {}),
                        item_data.get('category'),
                        {'use_cache': True}
                    )
                    
                    comparisons.append({
                        'item_index': i,
                        'item_id': item_data.get('id', f"item_{i}"),
                        'estimated_value': price_estimate['estimated_value'],
                        'confidence': price_estimate['confidence_score'],
                        'price_range': price_estimate['price_range'],
                        'category': item_data.get('category', 'unknown')
                    })
                    
                except Exception as e:
                    self.log_error(e, f"compare_prices_item_{i}")
                    comparisons.append({
                        'item_index': i,
                        'item_id': item_data.get('id', f"item_{i}"),
                        'error': str(e)
                    })
            
            # Calculate comparison statistics
            successful_comparisons = [c for c in comparisons if 'estimated_value' in c]
            
            if successful_comparisons:
                values = [c['estimated_value'] for c in successful_comparisons]
                comparison_stats = {
                    'highest_value': max(values),
                    'lowest_value': min(values),
                    'average_value': sum(values) / len(values),
                    'value_range': max(values) - min(values),
                    'total_items': len(comparisons),
                    'successful_estimates': len(successful_comparisons)
                }
            else:
                comparison_stats = {
                    'total_items': len(comparisons),
                    'successful_estimates': 0,
                    'error': 'No successful price estimates'
                }
            
            result = {
                'comparison_type': comparison_type,
                'items': comparisons,
                'statistics': comparison_stats,
                'compared_at': datetime.utcnow().isoformat()
            }
            
            log_service_result("PriceService", "compare_prices", True, 
                             successful=len(successful_comparisons), total=len(comparisons))
            
            return result
            
        except Exception as e:
            self.log_error(e, "compare_prices")
            raise AIProcessingError(f"Price comparison failed: {str(e)}")
    
    def validate_price_estimate(self, estimate_data: Dict) -> Dict:
        """Validate a price estimate against market data"""
        log_service_call("PriceService", "validate_price_estimate")
        
        try:
            estimated_value = estimate_data.get('estimated_value', 0)
            category = estimate_data.get('category', 'unknown')
            confidence = estimate_data.get('confidence_score', 0)
            
            # Get market trends for validation
            market_trends = self.market_service.get_market_trends(category)
            
            # Validation criteria
            validation_result = {
                'is_valid': True,
                'validation_score': 0.0,
                'issues': [],
                'warnings': [],
                'recommendations': []
            }
            
            # Check confidence threshold
            if confidence < 0.5:
                validation_result['issues'].append(f"Low confidence score: {confidence:.2f}")
                validation_result['is_valid'] = False
            elif confidence < 0.7:
                validation_result['warnings'].append(f"Moderate confidence: {confidence:.2f}")
            
            # Check price reasonableness
            if estimated_value <= 0:
                validation_result['issues'].append("Invalid price: must be positive")
                validation_result['is_valid'] = False
            elif estimated_value > 1000000:  # $1M threshold
                validation_result['warnings'].append("Very high estimated value")
            
            # Check market activity
            if market_trends.get('recent_activity', 0) < 5:
                validation_result['warnings'].append("Low market activity for this category")
            
            # Calculate validation score
            score_factors = []
            score_factors.append(confidence)
            
            if market_trends.get('trend_strength', 0) > 0.5:
                score_factors.append(0.8)  # Strong market trend
            else:
                score_factors.append(0.6)  # Weak market trend
            
            if len(validation_result['issues']) == 0:
                score_factors.append(0.9)  # No critical issues
            else:
                score_factors.append(0.3)  # Has critical issues
            
            validation_result['validation_score'] = sum(score_factors) / len(score_factors)
            
            # Add recommendations
            if validation_result['validation_score'] < 0.6:
                validation_result['recommendations'].append("Consider gathering more comparable data")
            
            if market_trends.get('price_volatility', 0) > 0.3:
                validation_result['recommendations'].append("High price volatility - consider multiple estimates")
            
            log_service_result("PriceService", "validate_price_estimate", True, 
                             is_valid=validation_result['is_valid'],
                             score=validation_result['validation_score'])
            
            return validation_result
            
        except Exception as e:
            self.log_error(e, "validate_price_estimate")
            raise AIProcessingError(f"Price validation failed: {str(e)}")
    
    def _generate_cache_key(
        self,
        embeddings: Dict,
        features: Dict,
        category: Optional[str],
        options: Dict
    ) -> str:
        """Generate cache key for price estimation"""
        try:
            # Create a deterministic representation of the input
            cache_data = {
                'embeddings_hash': self._hash_embeddings(embeddings),
                'features_hash': self._hash_dict(features),
                'category': category,
                'options': {k: v for k, v in options.items() if k in ['target_condition', 'similarity_threshold']}
            }
            
            # Generate hash
            cache_string = json.dumps(cache_data, sort_keys=True)
            cache_key = hashlib.md5(cache_string.encode()).hexdigest()
            
            return f"price_estimate_{cache_key}"
            
        except Exception as e:
            self.log_error(e, "_generate_cache_key")
            return f"price_estimate_{datetime.utcnow().timestamp()}"
    
    def _hash_embeddings(self, embeddings: Dict) -> str:
        """Generate hash for embeddings"""
        try:
            # Extract key embedding vectors for hashing
            key_vectors = []
            
            for key in ['multimodal_image', 'combined_0', 'objects_0']:
                if key in embeddings and 'vector' in embeddings[key]:
                    # Use first and last few values for hash (for performance)
                    vector = embeddings[key]['vector']
                    if len(vector) > 10:
                        sample = vector[:5] + vector[-5:]
                    else:
                        sample = vector
                    key_vectors.extend(sample)
            
            if key_vectors:
                # Round to reduce floating point variations
                rounded_vectors = [round(v, 4) for v in key_vectors]
                return hashlib.md5(str(rounded_vectors).encode()).hexdigest()[:16]
            else:
                return "no_embeddings"
                
        except Exception:
            return "embedding_hash_error"
    
    def _hash_dict(self, data: Dict) -> str:
        """Generate hash for dictionary data"""
        try:
            data_string = json.dumps(data, sort_keys=True)
            return hashlib.md5(data_string.encode()).hexdigest()[:16]
        except Exception:
            return "dict_hash_error"
    
    def _get_cached_result(self, cache_key: str) -> Optional[Dict]:
        """Get cached result if not expired"""
        try:
            if cache_key in self.cache and cache_key in self.cache_timestamps:
                cached_time = self.cache_timestamps[cache_key]
                if datetime.utcnow() - cached_time < timedelta(seconds=self.cache_ttl):
                    return self.cache[cache_key]
                else:
                    # Remove expired cache
                    del self.cache[cache_key]
                    del self.cache_timestamps[cache_key]
            
            return None
            
        except Exception as e:
            self.log_error(e, "_get_cached_result")
            return None
    
    def _cache_result(self, cache_key: str, result: Dict):
        """Cache result with timestamp"""
        try:
            self.cache[cache_key] = result
            self.cache_timestamps[cache_key] = datetime.utcnow()
            
            # Simple cache cleanup (remove oldest if too many)
            if len(self.cache) > 1000:
                oldest_key = min(self.cache_timestamps.keys(), key=self.cache_timestamps.get)
                del self.cache[oldest_key]
                del self.cache_timestamps[oldest_key]
                
        except Exception as e:
            self.log_error(e, "_cache_result")
    
    def _generate_mock_price_history(self, item_id: str, days: int) -> List[Dict]:
        """Generate mock price history for testing"""
        history = []
        base_price = 100.0
        current_date = datetime.utcnow()
        
        for i in range(days):
            date = current_date - timedelta(days=i)
            # Add some variation to the price
            variation = 0.9 + 0.2 * (i % 7) / 7  # Weekly cycles
            price = base_price * variation
            
            history.append({
                'date': date.isoformat(),
                'price': round(price, 2),
                'currency': 'USD',
                'source': 'mock_data'
            })
        
        return list(reversed(history))  # Chronological order
    
    def _analyze_price_history_trends(self, history: List[Dict]) -> Dict:
        """Analyze trends in price history"""
        try:
            if len(history) < 2:
                return {'trend': 'insufficient_data'}
            
            prices = [item['price'] for item in history]
            
            # Simple trend analysis
            first_half = prices[:len(prices)//2]
            second_half = prices[len(prices)//2:]
            
            first_avg = sum(first_half) / len(first_half)
            second_avg = sum(second_half) / len(second_half)
            
            change_pct = ((second_avg - first_avg) / first_avg) * 100
            
            if change_pct > 5:
                trend = 'increasing'
            elif change_pct < -5:
                trend = 'decreasing'
            else:
                trend = 'stable'
            
            # Calculate volatility
            import statistics
            volatility = statistics.stdev(prices) / statistics.mean(prices)
            
            return {
                'trend': trend,
                'change_percentage': round(change_pct, 1),
                'volatility': round(volatility, 3),
                'current_price': prices[-1],
                'average_price': round(statistics.mean(prices), 2),
                'price_range': {
                    'min': min(prices),
                    'max': max(prices)
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze price history trends: {e}")
            return {'trend': 'analysis_error'}
    
    def clear_cache(self):
        """Clear the price estimation cache"""
        self.cache.clear()
        self.cache_timestamps.clear()
        logger.info("Price estimation cache cleared")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        return {
            'cache_size': len(self.cache),
            'cache_ttl_seconds': self.cache_ttl,
            'oldest_entry': min(self.cache_timestamps.values()) if self.cache_timestamps else None,
            'newest_entry': max(self.cache_timestamps.values()) if self.cache_timestamps else None
        }
    
    def health_check(self) -> bool:
        """Health check for price service"""
        try:
            # Check underlying market service
            return self.market_service.health_check()
        except Exception as e:
            self.log_error(e, "health_check")
            return False

# Register service
registry.register("price_service", PriceService, singleton=False)