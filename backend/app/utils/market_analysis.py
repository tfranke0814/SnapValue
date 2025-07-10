import statistics
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from dataclasses import dataclass

from app.utils.logging import get_logger
from app.utils.exceptions import ValidationError, AIProcessingError

logger = get_logger(__name__)

@dataclass
class MarketInsight:
    """Data class for market insights"""
    category: str
    average_price: float
    price_range: Tuple[float, float]
    market_activity: int
    trend_direction: str
    confidence: float
    top_features: List[str]
    seasonal_patterns: Dict
    
@dataclass
class ComparableAnalysis:
    """Data class for comparable item analysis"""
    total_comparables: int
    close_matches: int
    price_distribution: Dict
    condition_analysis: Dict
    brand_analysis: Dict
    feature_importance: Dict
    market_positioning: str

class MarketAnalyzer:
    """Analyzer for market trends and insights"""
    
    def __init__(self):
        self.min_data_points = 5
        self.similarity_threshold = 0.7
        self.recent_period_days = 90
        self.trend_period_days = 365
        
        # Market categories and their characteristics
        self.category_characteristics = {
            'electronics': {
                'depreciation_rate': 0.15,  # 15% per year
                'seasonal_peak': [11, 12],  # Nov, Dec
                'brand_importance': 0.8
            },
            'collectibles': {
                'depreciation_rate': -0.05,  # 5% appreciation per year
                'seasonal_peak': [3, 4, 10, 11],  # Spring and Fall
                'brand_importance': 0.9
            },
            'clothing': {
                'depreciation_rate': 0.25,  # 25% per year
                'seasonal_peak': [2, 3, 8, 9],  # Season changes
                'brand_importance': 0.7
            },
            'furniture': {
                'depreciation_rate': 0.10,  # 10% per year
                'seasonal_peak': [4, 5, 8, 9],  # Moving seasons
                'brand_importance': 0.6
            },
            'art': {
                'depreciation_rate': -0.02,  # 2% appreciation per year
                'seasonal_peak': [5, 6, 10, 11],  # Auction seasons
                'brand_importance': 0.95
            }
        }
    
    def analyze_market_segment(
        self,
        market_data: List[Dict],
        target_category: Optional[str] = None,
        target_features: Optional[Dict] = None
    ) -> MarketInsight:
        """
        Analyze market segment for insights
        
        Args:
            market_data: List of market data items
            target_category: Specific category to analyze
            target_features: Target item features for comparison
            
        Returns:
            MarketInsight with segment analysis
        """
        logger.info(f"Analyzing market segment with {len(market_data)} items")
        
        try:
            # Filter data by category if specified
            if target_category:
                filtered_data = [item for item in market_data 
                               if item.get('category', '').lower() == target_category.lower()]
            else:
                filtered_data = market_data
            
            if len(filtered_data) < self.min_data_points:
                raise ValidationError(f"Insufficient data for market analysis: {len(filtered_data)}")
            
            # Extract prices and features
            prices = [float(item['price']) for item in filtered_data if item.get('price')]
            
            # Calculate price statistics
            avg_price = statistics.mean(prices)
            price_range = (min(prices), max(prices))
            
            # Analyze market activity
            recent_cutoff = datetime.utcnow() - timedelta(days=self.recent_period_days)
            recent_items = [item for item in filtered_data 
                          if self._parse_date(item.get('scraped_at', item.get('created_at'))) >= recent_cutoff]
            market_activity = len(recent_items)
            
            # Analyze trends
            trend_direction = self._analyze_price_trend(filtered_data)
            
            # Extract top features
            top_features = self._extract_top_features(filtered_data)
            
            # Analyze seasonal patterns
            seasonal_patterns = self._analyze_seasonal_patterns(filtered_data)
            
            # Calculate confidence
            confidence = self._calculate_market_confidence(filtered_data, target_features)
            
            category = target_category or self._determine_primary_category(filtered_data)
            
            insight = MarketInsight(
                category=category,
                average_price=round(avg_price, 2),
                price_range=(round(price_range[0], 2), round(price_range[1], 2)),
                market_activity=market_activity,
                trend_direction=trend_direction,
                confidence=round(confidence, 2),
                top_features=top_features,
                seasonal_patterns=seasonal_patterns
            )
            
            logger.info(f"Market segment analysis complete for {category}: "
                       f"avg ${avg_price:.2f}, trend: {trend_direction}")
            
            return insight
            
        except Exception as e:
            logger.error(f"Failed to analyze market segment: {e}")
            raise AIProcessingError(f"Market segment analysis failed: {str(e)}")
    
    def analyze_comparable_items(
        self,
        target_item_features: Dict,
        market_data: List[Dict],
        similarity_scores: Optional[List[float]] = None
    ) -> ComparableAnalysis:
        """
        Analyze comparable items for the target item
        
        Args:
            target_item_features: Features of target item
            market_data: Market data for comparison
            similarity_scores: Optional similarity scores for each item
            
        Returns:
            ComparableAnalysis with comparable item insights
        """
        logger.info(f"Analyzing {len(market_data)} comparable items")
        
        try:
            # Filter close matches
            close_matches = []
            if similarity_scores:
                for i, (item, score) in enumerate(zip(market_data, similarity_scores)):
                    if score >= self.similarity_threshold:
                        close_matches.append({**item, 'similarity_score': score})
            else:
                close_matches = market_data
            
            # Price distribution analysis
            prices = [float(item['price']) for item in close_matches if item.get('price')]
            price_distribution = self._analyze_price_distribution(prices)
            
            # Condition analysis
            condition_analysis = self._analyze_conditions(close_matches)
            
            # Brand analysis
            brand_analysis = self._analyze_brands(close_matches)
            
            # Feature importance analysis
            feature_importance = self._analyze_feature_importance(
                target_item_features, close_matches, similarity_scores
            )
            
            # Market positioning
            market_positioning = self._determine_market_positioning(
                target_item_features, close_matches
            )
            
            analysis = ComparableAnalysis(
                total_comparables=len(market_data),
                close_matches=len(close_matches),
                price_distribution=price_distribution,
                condition_analysis=condition_analysis,
                brand_analysis=brand_analysis,
                feature_importance=feature_importance,
                market_positioning=market_positioning
            )
            
            logger.info(f"Comparable analysis complete: {len(close_matches)} close matches")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze comparable items: {e}")
            raise AIProcessingError(f"Comparable analysis failed: {str(e)}")
    
    def predict_market_value(
        self,
        item_features: Dict,
        market_data: List[Dict],
        time_horizon_days: int = 30
    ) -> Dict:
        """
        Predict future market value based on trends
        
        Args:
            item_features: Features of the item
            market_data: Historical market data
            time_horizon_days: Prediction horizon in days
            
        Returns:
            Dictionary with value predictions
        """
        logger.info(f"Predicting market value for {time_horizon_days} days ahead")
        
        try:
            category = item_features.get('category', 'unknown')
            current_price = self._estimate_current_value(item_features, market_data)
            
            # Get category characteristics
            category_info = self.category_characteristics.get(category.lower(), {
                'depreciation_rate': 0.0,
                'seasonal_peak': [],
                'brand_importance': 0.5
            })
            
            # Calculate trend-based adjustment
            trend_adjustment = self._calculate_trend_adjustment(market_data, time_horizon_days)
            
            # Calculate seasonal adjustment
            seasonal_adjustment = self._calculate_seasonal_adjustment(
                category_info, time_horizon_days
            )
            
            # Calculate depreciation/appreciation
            annual_rate = category_info['depreciation_rate']
            depreciation_adjustment = 1 + (annual_rate * time_horizon_days / 365)
            
            # Combine adjustments
            total_adjustment = trend_adjustment * seasonal_adjustment * depreciation_adjustment
            predicted_value = current_price * total_adjustment
            
            # Calculate confidence based on data quality
            confidence = self._calculate_prediction_confidence(market_data, time_horizon_days)
            
            prediction = {
                'current_estimated_value': round(current_price, 2),
                'predicted_value': round(predicted_value, 2),
                'value_change': round(predicted_value - current_price, 2),
                'percentage_change': round(((predicted_value - current_price) / current_price) * 100, 1),
                'confidence': round(confidence, 2),
                'factors': {
                    'trend_adjustment': round(trend_adjustment, 3),
                    'seasonal_adjustment': round(seasonal_adjustment, 3),
                    'depreciation_adjustment': round(depreciation_adjustment, 3)
                },
                'prediction_horizon_days': time_horizon_days,
                'category': category
            }
            
            logger.info(f"Value prediction complete: ${predicted_value:.2f} "
                       f"({prediction['percentage_change']:+.1f}%)")
            
            return prediction
            
        except Exception as e:
            logger.error(f"Failed to predict market value: {e}")
            raise AIProcessingError(f"Market value prediction failed: {str(e)}")
    
    def _analyze_price_trend(self, market_data: List[Dict]) -> str:
        """Analyze price trend direction"""
        try:
            # Sort by date
            dated_items = []
            for item in market_data:
                date = self._parse_date(item.get('scraped_at', item.get('created_at')))
                if date and item.get('price'):
                    dated_items.append((date, float(item['price'])))
            
            if len(dated_items) < 5:
                return 'insufficient_data'
            
            dated_items.sort(key=lambda x: x[0])
            
            # Split into recent and older periods
            mid_point = len(dated_items) // 2
            older_prices = [price for _, price in dated_items[:mid_point]]
            recent_prices = [price for _, price in dated_items[mid_point:]]
            
            older_avg = statistics.mean(older_prices)
            recent_avg = statistics.mean(recent_prices)
            
            change_pct = ((recent_avg - older_avg) / older_avg) * 100
            
            if change_pct > 5:
                return 'increasing'
            elif change_pct < -5:
                return 'decreasing'
            else:
                return 'stable'
                
        except Exception as e:
            logger.warning(f"Failed to analyze price trend: {e}")
            return 'unknown'
    
    def _extract_top_features(self, market_data: List[Dict]) -> List[str]:
        """Extract most common features from market data"""
        feature_counts = Counter()
        
        for item in market_data:
            # Extract from title and description
            title = item.get('title', '').lower()
            description = item.get('description', '').lower()
            
            # Simple keyword extraction
            keywords = []
            text = f"{title} {description}"
            
            # Common valuable keywords
            valuable_keywords = [
                'vintage', 'antique', 'rare', 'limited', 'original', 'authentic',
                'mint', 'new', 'sealed', 'brand', 'designer', 'handmade',
                'collection', 'art', 'signed', 'numbered', 'first', 'edition'
            ]
            
            for keyword in valuable_keywords:
                if keyword in text:
                    keywords.append(keyword)
            
            # Extract brand names (simplified)
            if 'brand' in item:
                keywords.append(item['brand'].lower())
            
            for keyword in keywords:
                feature_counts[keyword] += 1
        
        # Return top 10 features
        return [feature for feature, _ in feature_counts.most_common(10)]
    
    def _analyze_seasonal_patterns(self, market_data: List[Dict]) -> Dict:
        """Analyze seasonal patterns in market data"""
        monthly_activity = defaultdict(int)
        monthly_prices = defaultdict(list)
        
        for item in market_data:
            date = self._parse_date(item.get('scraped_at', item.get('created_at')))
            if date and item.get('price'):
                month = date.month
                monthly_activity[month] += 1
                monthly_prices[month].append(float(item['price']))
        
        patterns = {}
        for month in range(1, 13):
            if month in monthly_activity:
                patterns[f"month_{month}"] = {
                    'activity': monthly_activity[month],
                    'avg_price': statistics.mean(monthly_prices[month]) if monthly_prices[month] else 0
                }
        
        return patterns
    
    def _calculate_market_confidence(
        self,
        market_data: List[Dict],
        target_features: Optional[Dict] = None
    ) -> float:
        """Calculate confidence in market analysis"""
        confidence_factors = []
        
        # Data quantity factor
        data_count = len(market_data)
        quantity_factor = min(1.0, data_count / 50)
        confidence_factors.append(quantity_factor)
        
        # Data recency factor
        recent_cutoff = datetime.utcnow() - timedelta(days=90)
        recent_count = sum(1 for item in market_data 
                          if self._parse_date(item.get('scraped_at', item.get('created_at'))) >= recent_cutoff)
        recency_factor = min(1.0, recent_count / max(1, data_count))
        confidence_factors.append(recency_factor)
        
        # Price consistency factor
        prices = [float(item['price']) for item in market_data if item.get('price')]
        if len(prices) > 1:
            cv = statistics.stdev(prices) / statistics.mean(prices)
            consistency_factor = max(0.1, 1 - cv)
            confidence_factors.append(consistency_factor)
        
        return statistics.mean(confidence_factors) if confidence_factors else 0.5
    
    def _analyze_price_distribution(self, prices: List[float]) -> Dict:
        """Analyze price distribution statistics"""
        if not prices:
            return {}
        
        return {
            'mean': round(statistics.mean(prices), 2),
            'median': round(statistics.median(prices), 2),
            'std_dev': round(statistics.stdev(prices), 2) if len(prices) > 1 else 0,
            'min': round(min(prices), 2),
            'max': round(max(prices), 2),
            'percentile_25': round(np.percentile(prices, 25), 2),
            'percentile_75': round(np.percentile(prices, 75), 2)
        }
    
    def _analyze_conditions(self, items: List[Dict]) -> Dict:
        """Analyze condition distribution"""
        condition_counts = Counter()
        condition_prices = defaultdict(list)
        
        for item in items:
            condition = item.get('condition', 'unknown').lower()
            condition_counts[condition] += 1
            if item.get('price'):
                condition_prices[condition].append(float(item['price']))
        
        analysis = {}
        for condition, count in condition_counts.items():
            avg_price = statistics.mean(condition_prices[condition]) if condition_prices[condition] else 0
            analysis[condition] = {
                'count': count,
                'percentage': round((count / len(items)) * 100, 1),
                'avg_price': round(avg_price, 2)
            }
        
        return analysis
    
    def _analyze_brands(self, items: List[Dict]) -> Dict:
        """Analyze brand distribution and pricing"""
        brand_counts = Counter()
        brand_prices = defaultdict(list)
        
        for item in items:
            brand = item.get('brand', 'unknown').lower()
            brand_counts[brand] += 1
            if item.get('price'):
                brand_prices[brand].append(float(item['price']))
        
        analysis = {}
        for brand, count in brand_counts.most_common(10):
            avg_price = statistics.mean(brand_prices[brand]) if brand_prices[brand] else 0
            analysis[brand] = {
                'count': count,
                'avg_price': round(avg_price, 2)
            }
        
        return analysis
    
    def _analyze_feature_importance(
        self,
        target_features: Dict,
        comparable_items: List[Dict],
        similarity_scores: Optional[List[float]] = None
    ) -> Dict:
        """Analyze which features are most important for pricing"""
        # Simplified feature importance analysis
        # In a real implementation, you'd use more sophisticated methods
        
        feature_importance = {
            'brand': 0.3,
            'condition': 0.25,
            'age': 0.2,
            'rarity': 0.15,
            'size': 0.1
        }
        
        # Adjust based on category
        category = target_features.get('category', 'unknown').lower()
        if category in self.category_characteristics:
            brand_importance = self.category_characteristics[category]['brand_importance']
            feature_importance['brand'] = brand_importance
            
            # Redistribute remaining importance
            remaining = 1.0 - brand_importance
            other_features = ['condition', 'age', 'rarity', 'size']
            for feature in other_features:
                feature_importance[feature] = remaining / len(other_features)
        
        return feature_importance
    
    def _determine_market_positioning(
        self,
        target_features: Dict,
        comparable_items: List[Dict]
    ) -> str:
        """Determine market positioning of the target item"""
        if not comparable_items:
            return 'unknown'
        
        prices = [float(item['price']) for item in comparable_items if item.get('price')]
        if not prices:
            return 'unknown'
        
        avg_price = statistics.mean(prices)
        target_price_estimate = avg_price  # Simplified
        
        percentile_25 = np.percentile(prices, 25)
        percentile_75 = np.percentile(prices, 75)
        
        if target_price_estimate >= percentile_75:
            return 'premium'
        elif target_price_estimate <= percentile_25:
            return 'budget'
        else:
            return 'mid_market'
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime object"""
        if not date_str:
            return None
        
        try:
            # Try different date formats
            formats = [
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%dT%H:%M:%SZ',
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            return None
            
        except Exception:
            return None
    
    def _determine_primary_category(self, market_data: List[Dict]) -> str:
        """Determine primary category from market data"""
        category_counts = Counter()
        
        for item in market_data:
            category = item.get('category', 'unknown').lower()
            category_counts[category] += 1
        
        return category_counts.most_common(1)[0][0] if category_counts else 'unknown'
    
    def _estimate_current_value(self, item_features: Dict, market_data: List[Dict]) -> float:
        """Estimate current value of item based on market data"""
        prices = [float(item['price']) for item in market_data if item.get('price')]
        return statistics.mean(prices) if prices else 0.0
    
    def _calculate_trend_adjustment(self, market_data: List[Dict], days_ahead: int) -> float:
        """Calculate adjustment based on market trends"""
        trend = self._analyze_price_trend(market_data)
        
        # Simple trend adjustments
        adjustments = {
            'increasing': 1 + (0.01 * days_ahead / 30),  # 1% per month
            'decreasing': 1 - (0.01 * days_ahead / 30),  # -1% per month
            'stable': 1.0,
            'unknown': 1.0,
            'insufficient_data': 1.0
        }
        
        return adjustments.get(trend, 1.0)
    
    def _calculate_seasonal_adjustment(self, category_info: Dict, days_ahead: int) -> float:
        """Calculate seasonal adjustment"""
        target_date = datetime.utcnow() + timedelta(days=days_ahead)
        target_month = target_date.month
        
        seasonal_peaks = category_info.get('seasonal_peak', [])
        
        if target_month in seasonal_peaks:
            return 1.05  # 5% increase during peak season
        else:
            return 0.98  # 2% decrease during off-season
    
    def _calculate_prediction_confidence(self, market_data: List[Dict], days_ahead: int) -> float:
        """Calculate confidence in value prediction"""
        base_confidence = 0.8
        
        # Reduce confidence for longer predictions
        time_factor = max(0.3, 1 - (days_ahead / 365))
        
        # Reduce confidence for insufficient data
        data_factor = min(1.0, len(market_data) / 20)
        
        return base_confidence * time_factor * data_factor

# Utility functions
def analyze_market_for_category(
    market_data: List[Dict],
    category: str,
    target_features: Optional[Dict] = None
) -> MarketInsight:
    """Analyze market for specific category"""
    analyzer = MarketAnalyzer()
    return analyzer.analyze_market_segment(market_data, category, target_features)

def get_comparable_analysis(
    target_features: Dict,
    market_data: List[Dict],
    similarity_scores: Optional[List[float]] = None
) -> ComparableAnalysis:
    """Get comparable item analysis"""
    analyzer = MarketAnalyzer()
    return analyzer.analyze_comparable_items(target_features, market_data, similarity_scores)

def predict_future_value(
    item_features: Dict,
    market_data: List[Dict],
    days_ahead: int = 30
) -> Dict:
    """Predict future market value"""
    analyzer = MarketAnalyzer()
    return analyzer.predict_market_value(item_features, market_data, days_ahead)