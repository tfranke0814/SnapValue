import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
import json

from app.utils.logging import get_logger
from app.utils.exceptions import AIProcessingError, DatabaseError

logger = get_logger(__name__)

class SimilaritySearchEngine:
    """Engine for finding similar items using vector embeddings"""
    
    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self.similarity_threshold = 0.7
        self.max_results = 50
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            # Convert to numpy arrays
            a = np.array(vec1)
            b = np.array(vec2)
            
            # Calculate cosine similarity
            dot_product = np.dot(a, b)
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)
            
            if norm_a == 0 or norm_b == 0:
                return 0.0
            
            similarity = dot_product / (norm_a * norm_b)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Failed to calculate cosine similarity: {e}")
            return 0.0
    
    def euclidean_distance(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate Euclidean distance between two vectors"""
        try:
            a = np.array(vec1)
            b = np.array(vec2)
            
            distance = np.linalg.norm(a - b)
            return float(distance)
            
        except Exception as e:
            logger.error(f"Failed to calculate Euclidean distance: {e}")
            return float('inf')
    
    def find_similar_items_by_embedding(
        self,
        query_embedding: List[float],
        category: Optional[str] = None,
        limit: int = 20,
        similarity_threshold: float = 0.7
    ) -> List[Dict]:
        """
        Find similar items using embedding similarity
        
        Args:
            query_embedding: Query embedding vector
            category: Optional category filter
            limit: Maximum number of results
            similarity_threshold: Minimum similarity threshold
            
        Returns:
            List of similar items with similarity scores
        """
        if not self.db:
            raise DatabaseError("Database session required for similarity search")
        
        try:
            # Base query to get market data with embeddings
            base_query = """
                SELECT id, title, category, price, currency, embeddings, features
                FROM market_data 
                WHERE embeddings IS NOT NULL
            """
            
            params = {}
            
            # Add category filter if specified
            if category:
                base_query += " AND category = :category"
                params['category'] = category
            
            # Execute query
            result = self.db.execute(text(base_query), params)
            market_items = result.fetchall()
            
            similar_items = []
            
            for item in market_items:
                try:
                    # Parse embeddings JSON
                    embeddings = json.loads(item.embeddings) if isinstance(item.embeddings, str) else item.embeddings
                    
                    # Get the best embedding for comparison
                    item_embedding = self._extract_best_embedding(embeddings)
                    
                    if item_embedding:
                        # Calculate similarity
                        similarity = self.cosine_similarity(query_embedding, item_embedding)
                        
                        if similarity >= similarity_threshold:
                            similar_items.append({
                                'id': item.id,
                                'title': item.title,
                                'category': item.category,
                                'price': float(item.price),
                                'currency': item.currency,
                                'similarity': similarity,
                                'features': json.loads(item.features) if item.features else {}
                            })
                
                except Exception as e:
                    logger.warning(f"Failed to process item {item.id}: {e}")
                    continue
            
            # Sort by similarity (descending) and limit results
            similar_items.sort(key=lambda x: x['similarity'], reverse=True)
            return similar_items[:limit]
            
        except Exception as e:
            logger.error(f"Failed to find similar items: {e}")
            raise DatabaseError(f"Similarity search failed: {str(e)}")
    
    def _extract_best_embedding(self, embeddings: Dict) -> Optional[List[float]]:
        """Extract the best embedding vector for comparison"""
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
    
    def find_similar_by_features(
        self,
        query_features: Dict,
        category: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict]:
        """
        Find similar items using feature matching
        
        Args:
            query_features: Features to match against
            category: Optional category filter
            limit: Maximum number of results
            
        Returns:
            List of similar items with feature match scores
        """
        if not self.db:
            raise DatabaseError("Database session required for feature search")
        
        try:
            # Base query
            base_query = """
                SELECT id, title, category, price, currency, features
                FROM market_data 
                WHERE features IS NOT NULL
            """
            
            params = {}
            
            # Add category filter if specified
            if category:
                base_query += " AND category = :category"
                params['category'] = category
            
            # Execute query
            result = self.db.execute(text(base_query), params)
            market_items = result.fetchall()
            
            similar_items = []
            
            for item in market_items:
                try:
                    # Parse features JSON
                    item_features = json.loads(item.features) if isinstance(item.features, str) else item.features
                    
                    # Calculate feature similarity
                    feature_score = self._calculate_feature_similarity(query_features, item_features)
                    
                    if feature_score > 0:
                        similar_items.append({
                            'id': item.id,
                            'title': item.title,
                            'category': item.category,
                            'price': float(item.price),
                            'currency': item.currency,
                            'feature_score': feature_score,
                            'features': item_features
                        })
                
                except Exception as e:
                    logger.warning(f"Failed to process item features {item.id}: {e}")
                    continue
            
            # Sort by feature score (descending) and limit results
            similar_items.sort(key=lambda x: x['feature_score'], reverse=True)
            return similar_items[:limit]
            
        except Exception as e:
            logger.error(f"Failed to find similar items by features: {e}")
            raise DatabaseError(f"Feature search failed: {str(e)}")
    
    def _calculate_feature_similarity(self, features1: Dict, features2: Dict) -> float:
        """Calculate similarity score between two feature sets"""
        try:
            total_score = 0.0
            weight_sum = 0.0
            
            # Feature weights
            feature_weights = {
                'categories': 0.3,
                'keywords': 0.25,
                'colors': 0.15,
                'text_content': 0.2,
                'has_faces': 0.1
            }
            
            # Compare categories
            if 'categories' in features1 and 'categories' in features2:
                categories1 = set(features1['categories'])
                categories2 = set(features2['categories'])
                if categories1 and categories2:
                    overlap = len(categories1.intersection(categories2))
                    union = len(categories1.union(categories2))
                    jaccard = overlap / union if union > 0 else 0
                    total_score += jaccard * feature_weights['categories']
                    weight_sum += feature_weights['categories']
            
            # Compare keywords
            if 'keywords' in features1 and 'keywords' in features2:
                keywords1 = set(features1['keywords'])
                keywords2 = set(features2['keywords'])
                if keywords1 and keywords2:
                    overlap = len(keywords1.intersection(keywords2))
                    union = len(keywords1.union(keywords2))
                    jaccard = overlap / union if union > 0 else 0
                    total_score += jaccard * feature_weights['keywords']
                    weight_sum += feature_weights['keywords']
            
            # Compare colors (simplified)
            if 'colors' in features1 and 'colors' in features2:
                colors1 = features1['colors']
                colors2 = features2['colors']
                if colors1 and colors2:
                    # Simple color similarity (could be improved with color distance)
                    color_similarity = 0.5  # Placeholder
                    total_score += color_similarity * feature_weights['colors']
                    weight_sum += feature_weights['colors']
            
            # Compare text content
            if 'text_content' in features1 and 'text_content' in features2:
                text1 = features1['text_content'].lower()
                text2 = features2['text_content'].lower()
                if text1 and text2:
                    # Simple text similarity (could use more sophisticated methods)
                    words1 = set(text1.split())
                    words2 = set(text2.split())
                    if words1 and words2:
                        overlap = len(words1.intersection(words2))
                        union = len(words1.union(words2))
                        text_sim = overlap / union if union > 0 else 0
                        total_score += text_sim * feature_weights['text_content']
                        weight_sum += feature_weights['text_content']
            
            # Compare face presence
            if 'has_faces' in features1 and 'has_faces' in features2:
                face_match = 1.0 if features1['has_faces'] == features2['has_faces'] else 0.0
                total_score += face_match * feature_weights['has_faces']
                weight_sum += feature_weights['has_faces']
            
            # Return normalized score
            return total_score / weight_sum if weight_sum > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Failed to calculate feature similarity: {e}")
            return 0.0
    
    def hybrid_search(
        self,
        query_embedding: List[float],
        query_features: Dict,
        category: Optional[str] = None,
        limit: int = 20,
        embedding_weight: float = 0.7,
        feature_weight: float = 0.3
    ) -> List[Dict]:
        """
        Hybrid search combining embedding and feature similarity
        
        Args:
            query_embedding: Query embedding vector
            query_features: Query features
            category: Optional category filter
            limit: Maximum number of results
            embedding_weight: Weight for embedding similarity
            feature_weight: Weight for feature similarity
            
        Returns:
            List of similar items with combined scores
        """
        try:
            # Get embedding-based results
            embedding_results = self.find_similar_items_by_embedding(
                query_embedding, category, limit * 2, 0.5  # Lower threshold for more candidates
            )
            
            # Get feature-based results
            feature_results = self.find_similar_by_features(
                query_features, category, limit * 2
            )
            
            # Combine results
            combined_results = {}
            
            # Add embedding results
            for item in embedding_results:
                item_id = item['id']
                combined_results[item_id] = {
                    **item,
                    'embedding_similarity': item['similarity'],
                    'feature_similarity': 0.0,
                    'combined_score': item['similarity'] * embedding_weight
                }
            
            # Add/update with feature results
            for item in feature_results:
                item_id = item['id']
                if item_id in combined_results:
                    # Update existing item
                    combined_results[item_id]['feature_similarity'] = item['feature_score']
                    combined_results[item_id]['combined_score'] = (
                        combined_results[item_id]['embedding_similarity'] * embedding_weight +
                        item['feature_score'] * feature_weight
                    )
                else:
                    # Add new item
                    combined_results[item_id] = {
                        **item,
                        'embedding_similarity': 0.0,
                        'feature_similarity': item['feature_score'],
                        'combined_score': item['feature_score'] * feature_weight
                    }
            
            # Convert to list and sort by combined score
            final_results = list(combined_results.values())
            final_results.sort(key=lambda x: x['combined_score'], reverse=True)
            
            return final_results[:limit]
            
        except Exception as e:
            logger.error(f"Failed to perform hybrid search: {e}")
            raise AIProcessingError(f"Hybrid search failed: {str(e)}")

# Utility functions
def find_similar_items(
    query_embedding: List[float],
    db: Session,
    category: Optional[str] = None,
    limit: int = 20,
    threshold: float = 0.7
) -> List[Dict]:
    """Find similar items using embedding similarity"""
    engine = SimilaritySearchEngine(db)
    return engine.find_similar_items_by_embedding(query_embedding, category, limit, threshold)

def search_by_features(
    query_features: Dict,
    db: Session,
    category: Optional[str] = None,
    limit: int = 20
) -> List[Dict]:
    """Search items by feature matching"""
    engine = SimilaritySearchEngine(db)
    return engine.find_similar_by_features(query_features, category, limit)

def hybrid_item_search(
    query_embedding: List[float],
    query_features: Dict,
    db: Session,
    category: Optional[str] = None,
    limit: int = 20
) -> List[Dict]:
    """Hybrid search combining embeddings and features"""
    engine = SimilaritySearchEngine(db)
    return engine.hybrid_search(query_embedding, query_features, category, limit)