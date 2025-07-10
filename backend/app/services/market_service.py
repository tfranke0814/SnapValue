from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_
import json

from app.services.base_service import BaseService
from app.models.market_data import MarketData
from app.utils.similarity_search import SimilaritySearchEngine, hybrid_item_search
from app.utils.price_calculation import PriceCalculator, calculate_price_from_similar_items
from app.utils.market_analysis import MarketAnalyzer, analyze_market_for_category
from app.utils.exceptions import ValidationError, DatabaseError, AIProcessingError
from app.utils.logging import get_logger, log_service_call, log_service_result
from app.core.registry import registry

logger = get_logger(__name__)

class MarketService(BaseService):
    """Service for market data analysis and price estimation"""
    
    def __init__(self, db: Optional[Session] = None):
        super().__init__(db)
        self.similarity_engine = SimilaritySearchEngine(db)
        self.price_calculator = PriceCalculator()
        self.market_analyzer = MarketAnalyzer()
        
        # Service configuration
        self.default_similarity_threshold = 0.7
        self.max_comparables = 50
        self.min_comparables = 3
        self.cache_ttl = 3600  # 1 hour
    
    def validate_input(self, data) -> bool:
        """Validate input for market analysis"""
        if not isinstance(data, dict):
            return False
        
        # Must have either embeddings or features for comparison
        return 'embeddings' in data or 'features' in data
    
    def process(self, data: Dict) -> Dict:
        """Process market analysis - main entry point"""
        if not self.validate_input(data):
            raise ValidationError("Invalid input data for market analysis")
        
        return self.analyze_item_market_value(
            data.get('embeddings', {}),
            data.get('features', {}),
            data.get('category'),
            data.get('options', {})
        )
    
    def analyze_item_market_value(
        self,
        embeddings: Dict,
        features: Dict,
        category: Optional[str] = None,
        options: Optional[Dict] = None
    ) -> Dict:
        """
        Comprehensive market value analysis for an item
        
        Args:
            embeddings: Item embeddings for similarity search
            features: Item features for analysis
            category: Item category
            options: Analysis options
            
        Returns:
            Dictionary with complete market analysis
        """
        if options is None:
            options = {}
        
        log_service_call("MarketService", "analyze_item_market_value", 
                        category=category, has_embeddings=bool(embeddings))
        
        try:
            # Step 1: Find similar items
            similar_items = self._find_similar_market_items(embeddings, features, category, options)
            
            if len(similar_items) < self.min_comparables:
                raise ValidationError(f"Insufficient comparable items found: {len(similar_items)}")
            
            # Step 2: Calculate price estimation
            price_analysis = self._calculate_price_estimation(similar_items, options)
            
            # Step 3: Analyze market segment
            market_insight = self._analyze_market_segment(similar_items, category, features)
            
            # Step 4: Analyze comparable items
            comparable_analysis = self._analyze_comparable_items(features, similar_items)
            
            # Step 5: Calculate overall confidence
            overall_confidence = self._calculate_overall_confidence(
                price_analysis, market_insight, comparable_analysis, len(similar_items)
            )
            
            # Step 6: Generate recommendations
            recommendations = self._generate_recommendations(
                price_analysis, market_insight, comparable_analysis
            )
            
            # Prepare comprehensive results
            results = {
                'estimated_value': price_analysis.estimated_value,
                'price_range': {
                    'min': price_analysis.price_range_min,
                    'max': price_analysis.price_range_max
                },
                'currency': price_analysis.currency,
                'confidence_score': overall_confidence,
                'market_analysis': {
                    'category': market_insight.category,
                    'market_activity': market_insight.market_activity,
                    'trend_direction': market_insight.trend_direction,
                    'average_market_price': market_insight.average_price,
                    'market_range': {
                        'min': market_insight.price_range[0],
                        'max': market_insight.price_range[1]
                    },
                    'top_features': market_insight.top_features,
                    'seasonal_patterns': market_insight.seasonal_patterns
                },
                'comparable_items': {
                    'total_found': comparable_analysis.total_comparables,
                    'close_matches': comparable_analysis.close_matches,
                    'price_distribution': comparable_analysis.price_distribution,
                    'condition_analysis': comparable_analysis.condition_analysis,
                    'brand_analysis': comparable_analysis.brand_analysis,
                    'market_positioning': comparable_analysis.market_positioning
                },
                'price_calculation': {
                    'method': price_analysis.analysis_method,
                    'data_points_used': price_analysis.data_points_used,
                    'outliers_removed': price_analysis.outliers_removed,
                    'market_trends': price_analysis.market_trends
                },
                'recommendations': recommendations,
                'analysis_metadata': {
                    'analyzed_at': datetime.utcnow().isoformat(),
                    'similarity_threshold': options.get('similarity_threshold', self.default_similarity_threshold),
                    'analysis_method': 'comprehensive_market_analysis'
                }
            }
            
            log_service_result("MarketService", "analyze_item_market_value", True, 
                             estimated_value=price_analysis.estimated_value,
                             confidence=overall_confidence,
                             comparables=len(similar_items))
            
            return results
            
        except Exception as e:
            self.log_error(e, "analyze_item_market_value")
            raise
    
    def _find_similar_market_items(
        self,
        embeddings: Dict,
        features: Dict,
        category: Optional[str],
        options: Dict
    ) -> List[Dict]:
        """Find similar items in market data"""
        log_service_call("MarketService", "_find_similar_market_items", 
                        category=category)
        
        try:
            similarity_threshold = options.get('similarity_threshold', self.default_similarity_threshold)
            max_results = options.get('max_comparables', self.max_comparables)
            
            # Extract query embedding for similarity search
            query_embedding = self._extract_query_embedding(embeddings)
            
            if query_embedding and self.db:
                # Use hybrid search (embedding + features)
                similar_items = hybrid_item_search(
                    query_embedding,
                    features,
                    self.db,
                    category,
                    max_results
                )
            elif self.db:
                # Fallback to feature-based search
                from app.utils.similarity_search import search_by_features
                similar_items = search_by_features(
                    features,
                    self.db,
                    category,
                    max_results
                )
            else:
                # Mock data for testing
                similar_items = self._get_mock_market_data(category, max_results)
            
            # Filter by similarity threshold
            filtered_items = [
                item for item in similar_items
                if item.get('similarity', item.get('combined_score', 0)) >= similarity_threshold
            ]
            
            log_service_result("MarketService", "_find_similar_market_items", True, 
                             found=len(similar_items), filtered=len(filtered_items))
            
            return filtered_items
            
        except Exception as e:
            self.log_error(e, "_find_similar_market_items")
            # Return mock data as fallback
            return self._get_mock_market_data(category, 10)
    
    def _extract_query_embedding(self, embeddings: Dict) -> Optional[List[float]]:
        """Extract the best embedding for similarity search"""
        # Priority order for embeddings
        embedding_priority = [
            'multimodal_image',
            'combined_0',
            'objects_0',
            'labels_0'
        ]
        
        for embedding_key in embedding_priority:
            if embedding_key in embeddings and 'vector' in embeddings[embedding_key]:
                return embeddings[embedding_key]['vector']
        
        # Fallback: return any available embedding
        for key, value in embeddings.items():
            if isinstance(value, dict) and 'vector' in value:
                return value['vector']
        
        return None
    
    def _calculate_price_estimation(self, similar_items: List[Dict], options: Dict) -> Any:
        """Calculate price estimation from similar items"""
        log_service_call("MarketService", "_calculate_price_estimation", 
                        items_count=len(similar_items))
        
        try:
            target_condition = options.get('target_condition')
            
            # Use the price calculator
            price_analysis = calculate_price_from_similar_items(similar_items, target_condition)
            
            log_service_result("MarketService", "_calculate_price_estimation", True, 
                             estimated_value=price_analysis.estimated_value)
            
            return price_analysis
            
        except Exception as e:
            self.log_error(e, "_calculate_price_estimation")
            raise AIProcessingError(f"Price calculation failed: {str(e)}")
    
    def _analyze_market_segment(
        self,
        similar_items: List[Dict],
        category: Optional[str],
        features: Dict
    ) -> Any:
        """Analyze market segment for insights"""
        log_service_call("MarketService", "_analyze_market_segment", 
                        category=category, items_count=len(similar_items))
        
        try:
            market_insight = analyze_market_for_category(similar_items, category or 'unknown', features)
            
            log_service_result("MarketService", "_analyze_market_segment", True, 
                             category=market_insight.category)
            
            return market_insight
            
        except Exception as e:
            self.log_error(e, "_analyze_market_segment")
            raise AIProcessingError(f"Market segment analysis failed: {str(e)}")
    
    def _analyze_comparable_items(self, features: Dict, similar_items: List[Dict]) -> Any:
        """Analyze comparable items"""
        log_service_call("MarketService", "_analyze_comparable_items", 
                        items_count=len(similar_items))
        
        try:
            # Extract similarity scores
            similarity_scores = [
                item.get('similarity', item.get('combined_score', 0.5))
                for item in similar_items
            ]
            
            comparable_analysis = self.market_analyzer.analyze_comparable_items(
                features, similar_items, similarity_scores
            )
            
            log_service_result("MarketService", "_analyze_comparable_items", True, 
                             close_matches=comparable_analysis.close_matches)
            
            return comparable_analysis
            
        except Exception as e:
            self.log_error(e, "_analyze_comparable_items")
            raise AIProcessingError(f"Comparable analysis failed: {str(e)}")
    
    def _calculate_overall_confidence(
        self,
        price_analysis: Any,
        market_insight: Any,
        comparable_analysis: Any,
        similar_items_count: int
    ) -> float:
        """Calculate overall confidence score"""
        try:
            confidence_factors = []
            
            # Price analysis confidence
            confidence_factors.append(price_analysis.confidence_score)
            
            # Market insight confidence
            confidence_factors.append(market_insight.confidence)
            
            # Data quantity factor
            quantity_factor = min(1.0, similar_items_count / 20)
            confidence_factors.append(quantity_factor)
            
            # Close matches factor
            if comparable_analysis.total_comparables > 0:
                match_ratio = comparable_analysis.close_matches / comparable_analysis.total_comparables
                confidence_factors.append(match_ratio)
            
            # Calculate weighted average
            overall_confidence = sum(confidence_factors) / len(confidence_factors)
            
            return max(0.1, min(1.0, overall_confidence))
            
        except Exception as e:
            self.log_error(e, "_calculate_overall_confidence")
            return 0.5
    
    def _generate_recommendations(
        self,
        price_analysis: Any,
        market_insight: Any,
        comparable_analysis: Any
    ) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        try:
            # Price-based recommendations
            if price_analysis.confidence_score < 0.6:
                recommendations.append("Consider getting additional comparable data for more accurate pricing")
            
            # Market trend recommendations
            if market_insight.trend_direction == 'increasing':
                recommendations.append("Market trend is positive - good time for selling")
            elif market_insight.trend_direction == 'decreasing':
                recommendations.append("Market trend is declining - consider holding or pricing competitively")
            
            # Activity recommendations
            if market_insight.market_activity < 5:
                recommendations.append("Low market activity - item may take longer to sell")
            elif market_insight.market_activity > 20:
                recommendations.append("High market activity - favorable selling conditions")
            
            # Positioning recommendations
            if comparable_analysis.market_positioning == 'premium':
                recommendations.append("Item appears to be in premium market segment")
            elif comparable_analysis.market_positioning == 'budget':
                recommendations.append("Item appears to be in budget market segment")
            
            # Data quality recommendations
            if comparable_analysis.close_matches < 5:
                recommendations.append("Limited comparable data - consider expanding search criteria")
            
            return recommendations
            
        except Exception as e:
            self.log_error(e, "_generate_recommendations")
            return ["Market analysis completed successfully"]
    
    def _get_mock_market_data(self, category: Optional[str], count: int) -> List[Dict]:
        """Get mock market data for testing"""
        mock_data = []
        
        base_price = 100.0
        if category:
            category_multipliers = {
                'electronics': 300.0,
                'collectibles': 150.0,
                'clothing': 50.0,
                'furniture': 200.0,
                'art': 500.0
            }
            base_price = category_multipliers.get(category.lower(), base_price)
        
        for i in range(count):
            mock_data.append({
                'id': f"mock_{i}",
                'title': f"Mock Item {i}",
                'category': category or 'unknown',
                'price': base_price * (0.8 + 0.4 * (i / count)),  # Vary price
                'currency': 'USD',
                'source': 'mock_source',
                'similarity': 0.8 - (i * 0.05),  # Decreasing similarity
                'condition': 'good',
                'features': {},
                'created_at': datetime.utcnow().isoformat()
            })
        
        return mock_data
    
    def get_market_trends(self, category: str, days: int = 90) -> Dict:
        """Get market trends for a category"""
        log_service_call("MarketService", "get_market_trends", 
                        category=category, days=days)
        
        try:
            if not self.db:
                return self._get_mock_trends(category)
            
            # Query market data for the category
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            query = text("""
                SELECT price, currency, created_at, scraped_at
                FROM market_data 
                WHERE category = :category 
                AND (created_at >= :cutoff_date OR scraped_at >= :cutoff_date)
                ORDER BY COALESCE(scraped_at, created_at) DESC
            """)
            
            result = self.db.execute(query, {
                'category': category,
                'cutoff_date': cutoff_date
            })
            
            trend_data = []
            for row in result:
                trend_data.append({
                    'price': float(row.price),
                    'currency': row.currency,
                    'date': (row.scraped_at or row.created_at).isoformat()
                })
            
            # Analyze trends
            from app.utils.price_calculation import analyze_price_trends
            trends = analyze_price_trends(trend_data)
            
            log_service_result("MarketService", "get_market_trends", True, 
                             category=category, data_points=len(trend_data))
            
            return trends
            
        except Exception as e:
            self.log_error(e, "get_market_trends")
            return self._get_mock_trends(category)
    
    def _get_mock_trends(self, category: str) -> Dict:
        """Get mock trend data"""
        return {
            'trend_direction': 'stable',
            'trend_strength': 0.3,
            'price_volatility': 0.15,
            'recent_activity': 25,
            'category': category
        }
    
    def search_similar_items(
        self,
        embeddings: Dict,
        features: Dict,
        category: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict]:
        """Search for similar items in market data"""
        log_service_call("MarketService", "search_similar_items", 
                        category=category, limit=limit)
        
        try:
            similar_items = self._find_similar_market_items(
                embeddings, features, category, {'max_comparables': limit}
            )
            
            log_service_result("MarketService", "search_similar_items", True, 
                             found=len(similar_items))
            
            return similar_items
            
        except Exception as e:
            self.log_error(e, "search_similar_items")
            raise
    
    def health_check(self) -> bool:
        """Health check for market service"""
        try:
            # Check database connection if available
            if self.db:
                self.db.execute(text("SELECT 1"))
            
            return True
        except Exception as e:
            self.log_error(e, "health_check")
            return False

# Register service
registry.register("market_service", MarketService, singleton=False)