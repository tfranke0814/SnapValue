import statistics
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

from app.utils.logging import get_logger
from app.utils.exceptions import ValidationError

logger = get_logger(__name__)

@dataclass
class PriceDataPoint:
    """Data class for price information"""
    price: float
    currency: str
    source: str
    date: datetime
    condition: Optional[str] = None
    similarity_score: Optional[float] = None
    confidence: Optional[float] = None

@dataclass
class PriceAnalysis:
    """Data class for price analysis results"""
    estimated_value: float
    price_range_min: float
    price_range_max: float
    confidence_score: float
    currency: str
    data_points_used: int
    analysis_method: str
    market_trends: Dict
    outliers_removed: int
    last_updated: datetime

class PriceCalculator:
    """Calculator for item price estimation and analysis"""
    
    def __init__(self):
        self.min_data_points = 3
        self.max_data_points = 50
        self.outlier_threshold = 2.0  # Standard deviations
        self.similarity_weight = 0.4
        self.recency_weight = 0.3
        self.condition_weight = 0.2
        self.source_weight = 0.1
        
        # Source reliability weights
        self.source_weights = {
            'ebay': 0.8,
            'amazon': 0.9,
            'etsy': 0.7,
            'mercari': 0.6,
            'facebook_marketplace': 0.5,
            'craigslist': 0.4,
            'auction_house': 1.0,
            'retail_store': 0.9,
            'unknown': 0.3
        }
        
        # Condition adjustments
        self.condition_multipliers = {
            'mint': 1.2,
            'excellent': 1.1,
            'very_good': 1.0,
            'good': 0.9,
            'fair': 0.7,
            'poor': 0.5,
            'unknown': 0.8
        }
    
    def calculate_estimated_price(
        self,
        price_data: List[PriceDataPoint],
        target_condition: Optional[str] = None
    ) -> PriceAnalysis:
        """
        Calculate estimated price from market data
        
        Args:
            price_data: List of price data points
            target_condition: Target condition for estimation
            
        Returns:
            PriceAnalysis with estimated value and confidence
        """
        logger.info(f"Calculating price from {len(price_data)} data points")
        
        try:
            if len(price_data) < self.min_data_points:
                raise ValidationError(f"Insufficient data points: {len(price_data)} < {self.min_data_points}")
            
            # Filter and prepare data
            filtered_data = self._filter_and_prepare_data(price_data)
            
            if len(filtered_data) < self.min_data_points:
                raise ValidationError(f"Insufficient valid data points after filtering: {len(filtered_data)}")
            
            # Remove outliers
            cleaned_data, outliers_removed = self._remove_outliers(filtered_data)
            
            # Calculate weights for each data point
            weighted_data = self._calculate_weights(cleaned_data)
            
            # Calculate estimated price
            estimated_value = self._calculate_weighted_average(weighted_data)
            
            # Adjust for target condition
            if target_condition:
                estimated_value = self._adjust_for_condition(estimated_value, target_condition)
            
            # Calculate price range
            price_range = self._calculate_price_range(weighted_data, estimated_value)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(weighted_data, price_range)
            
            # Analyze market trends
            market_trends = self._analyze_market_trends(cleaned_data)
            
            # Determine primary currency
            currency = self._determine_currency(cleaned_data)
            
            analysis = PriceAnalysis(
                estimated_value=round(estimated_value, 2),
                price_range_min=round(price_range[0], 2),
                price_range_max=round(price_range[1], 2),
                confidence_score=round(confidence_score, 2),
                currency=currency,
                data_points_used=len(cleaned_data),
                analysis_method="weighted_average",
                market_trends=market_trends,
                outliers_removed=outliers_removed,
                last_updated=datetime.utcnow()
            )
            
            logger.info(f"Price calculation complete: ${analysis.estimated_value} {analysis.currency} "
                       f"(confidence: {analysis.confidence_score})")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to calculate estimated price: {e}")
            raise
    
    def _filter_and_prepare_data(self, price_data: List[PriceDataPoint]) -> List[PriceDataPoint]:
        """Filter and prepare price data for analysis"""
        filtered_data = []
        
        for point in price_data:
            # Basic validation
            if point.price <= 0:
                continue
            
            # Currency validation (convert if needed)
            if point.currency not in ['USD', 'EUR', 'GBP', 'CAD', 'AUD']:
                # For now, skip non-major currencies
                # In production, you'd want currency conversion
                continue
            
            # Age filter (last 2 years for most relevance)
            if point.date < datetime.utcnow() - timedelta(days=730):
                continue
            
            filtered_data.append(point)
        
        return filtered_data
    
    def _remove_outliers(self, price_data: List[PriceDataPoint]) -> Tuple[List[PriceDataPoint], int]:
        """Remove price outliers using statistical methods"""
        if len(price_data) < 5:
            return price_data, 0
        
        prices = [point.price for point in price_data]
        
        # Calculate Z-scores
        mean_price = statistics.mean(prices)
        std_price = statistics.stdev(prices)
        
        if std_price == 0:
            return price_data, 0
        
        cleaned_data = []
        outliers_removed = 0
        
        for point in price_data:
            z_score = abs((point.price - mean_price) / std_price)
            if z_score <= self.outlier_threshold:
                cleaned_data.append(point)
            else:
                outliers_removed += 1
        
        logger.debug(f"Removed {outliers_removed} outliers from {len(price_data)} data points")
        
        return cleaned_data, outliers_removed
    
    def _calculate_weights(self, price_data: List[PriceDataPoint]) -> List[Tuple[PriceDataPoint, float]]:
        """Calculate weights for each price data point"""
        weighted_data = []
        
        for point in price_data:
            weight = 1.0
            
            # Similarity weight
            if point.similarity_score is not None:
                weight *= (1 + point.similarity_score * self.similarity_weight)
            
            # Recency weight
            days_old = (datetime.utcnow() - point.date).days
            recency_factor = max(0.1, 1 - (days_old / 365))  # Decay over a year
            weight *= (1 + recency_factor * self.recency_weight)
            
            # Source reliability weight
            source_reliability = self.source_weights.get(point.source.lower(), 0.5)
            weight *= (1 + source_reliability * self.source_weight)
            
            # Condition weight
            if point.condition:
                condition_factor = self.condition_multipliers.get(point.condition.lower(), 0.8)
                weight *= (1 + condition_factor * self.condition_weight)
            
            # Confidence weight
            if point.confidence is not None:
                weight *= (1 + point.confidence * 0.1)
            
            weighted_data.append((point, weight))
        
        return weighted_data
    
    def _calculate_weighted_average(self, weighted_data: List[Tuple[PriceDataPoint, float]]) -> float:
        """Calculate weighted average price"""
        total_weighted_price = 0.0
        total_weight = 0.0
        
        for point, weight in weighted_data:
            total_weighted_price += point.price * weight
            total_weight += weight
        
        return total_weighted_price / total_weight if total_weight > 0 else 0.0
    
    def _adjust_for_condition(self, base_price: float, target_condition: str) -> float:
        """Adjust price based on target condition"""
        multiplier = self.condition_multipliers.get(target_condition.lower(), 1.0)
        return base_price * multiplier
    
    def _calculate_price_range(
        self,
        weighted_data: List[Tuple[PriceDataPoint, float]],
        estimated_value: float
    ) -> Tuple[float, float]:
        """Calculate price range (min, max)"""
        prices = [point.price for point, _ in weighted_data]
        
        # Use statistical methods for range
        if len(prices) >= 5:
            # Use percentiles for more robust range
            price_min = np.percentile(prices, 25)
            price_max = np.percentile(prices, 75)
            
            # Expand range slightly based on confidence
            range_expansion = (price_max - price_min) * 0.2
            price_min = max(0, price_min - range_expansion)
            price_max = price_max + range_expansion
        else:
            # Use min/max with some padding
            price_min = min(prices) * 0.8
            price_max = max(prices) * 1.2
        
        # Ensure estimated value is within range
        price_min = min(price_min, estimated_value * 0.7)
        price_max = max(price_max, estimated_value * 1.3)
        
        return price_min, price_max
    
    def _calculate_confidence_score(
        self,
        weighted_data: List[Tuple[PriceDataPoint, float]],
        price_range: Tuple[float, float]
    ) -> float:
        """Calculate confidence score for the price estimation"""
        confidence_factors = []
        
        # Data quantity factor
        data_count = len(weighted_data)
        quantity_factor = min(1.0, data_count / 20)  # Max confidence at 20+ data points
        confidence_factors.append(quantity_factor)
        
        # Price consistency factor
        prices = [point.price for point, _ in weighted_data]
        if len(prices) > 1:
            cv = statistics.stdev(prices) / statistics.mean(prices)  # Coefficient of variation
            consistency_factor = max(0.1, 1 - cv)  # Lower CV = higher confidence
            confidence_factors.append(consistency_factor)
        
        # Recency factor
        recent_count = sum(1 for point, _ in weighted_data 
                          if (datetime.utcnow() - point.date).days <= 90)
        recency_factor = min(1.0, recent_count / max(1, data_count))
        confidence_factors.append(recency_factor)
        
        # Similarity factor
        similarity_scores = [point.similarity_score for point, _ in weighted_data 
                           if point.similarity_score is not None]
        if similarity_scores:
            avg_similarity = statistics.mean(similarity_scores)
            confidence_factors.append(avg_similarity)
        
        # Source reliability factor
        source_reliabilities = []
        for point, _ in weighted_data:
            reliability = self.source_weights.get(point.source.lower(), 0.5)
            source_reliabilities.append(reliability)
        
        if source_reliabilities:
            avg_source_reliability = statistics.mean(source_reliabilities)
            confidence_factors.append(avg_source_reliability)
        
        # Calculate overall confidence
        overall_confidence = statistics.mean(confidence_factors) if confidence_factors else 0.5
        
        return max(0.1, min(1.0, overall_confidence))
    
    def _analyze_market_trends(self, price_data: List[PriceDataPoint]) -> Dict:
        """Analyze market trends from price data"""
        trends = {
            'trend_direction': 'stable',
            'trend_strength': 0.0,
            'price_volatility': 0.0,
            'seasonal_patterns': {},
            'recent_activity': 0
        }
        
        try:
            if len(price_data) < 5:
                return trends
            
            # Sort by date
            sorted_data = sorted(price_data, key=lambda x: x.date)
            
            # Calculate trend
            prices = [point.price for point in sorted_data]
            dates = [(point.date - sorted_data[0].date).days for point in sorted_data]
            
            if len(prices) > 2:
                # Simple linear trend
                correlation = np.corrcoef(dates, prices)[0, 1]
                
                if correlation > 0.3:
                    trends['trend_direction'] = 'increasing'
                elif correlation < -0.3:
                    trends['trend_direction'] = 'decreasing'
                else:
                    trends['trend_direction'] = 'stable'
                
                trends['trend_strength'] = abs(correlation)
            
            # Calculate volatility
            if len(prices) > 1:
                price_changes = [abs(prices[i] - prices[i-1]) / prices[i-1] 
                               for i in range(1, len(prices))]
                trends['price_volatility'] = statistics.mean(price_changes)
            
            # Recent activity (last 30 days)
            recent_cutoff = datetime.utcnow() - timedelta(days=30)
            recent_count = sum(1 for point in price_data if point.date >= recent_cutoff)
            trends['recent_activity'] = recent_count
            
        except Exception as e:
            logger.warning(f"Failed to analyze market trends: {e}")
        
        return trends
    
    def _determine_currency(self, price_data: List[PriceDataPoint]) -> str:
        """Determine the primary currency from price data"""
        currency_counts = {}
        
        for point in price_data:
            currency_counts[point.currency] = currency_counts.get(point.currency, 0) + 1
        
        # Return most common currency
        return max(currency_counts, key=currency_counts.get) if currency_counts else 'USD'

# Utility functions
def calculate_price_from_similar_items(
    similar_items: List[Dict],
    target_condition: Optional[str] = None
) -> PriceAnalysis:
    """Calculate price from similar items data"""
    calculator = PriceCalculator()
    
    # Convert similar items to PriceDataPoint objects
    price_data = []
    
    for item in similar_items:
        try:
            price_point = PriceDataPoint(
                price=float(item['price']),
                currency=item.get('currency', 'USD'),
                source=item.get('source', 'unknown'),
                date=datetime.utcnow(),  # Use current date if not provided
                condition=item.get('condition'),
                similarity_score=item.get('similarity', item.get('feature_score')),
                confidence=item.get('confidence')
            )
            price_data.append(price_point)
        except (ValueError, KeyError) as e:
            logger.warning(f"Skipping invalid price data: {e}")
            continue
    
    return calculator.calculate_estimated_price(price_data, target_condition)

def analyze_price_trends(price_history: List[Dict]) -> Dict:
    """Analyze price trends from historical data"""
    calculator = PriceCalculator()
    
    # Convert to PriceDataPoint objects
    price_data = []
    for item in price_history:
        try:
            price_point = PriceDataPoint(
                price=float(item['price']),
                currency=item.get('currency', 'USD'),
                source=item.get('source', 'unknown'),
                date=datetime.fromisoformat(item['date']) if 'date' in item else datetime.utcnow()
            )
            price_data.append(price_point)
        except (ValueError, KeyError) as e:
            logger.warning(f"Skipping invalid price history item: {e}")
            continue
    
    return calculator._analyze_market_trends(price_data)