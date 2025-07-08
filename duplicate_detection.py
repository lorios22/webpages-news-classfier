import hashlib
import json
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import re

class DuplicateDetector:
    """
    Duplicate detection system for news articles using content hashing and similarity.
    """
    
    def __init__(self, memory_file: str = "duplicate_memory.json", retention_days: int = 7):
        self.memory_file = memory_file
        self.retention_days = retention_days
        self.memory = self._load_memory()
    
    def _load_memory(self) -> Dict:
        """Load duplicate detection memory from file."""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading duplicate memory: {e}")
                return {"articles": []}
        return {"articles": []}
    
    def _save_memory(self):
        """Save duplicate detection memory to file."""
        try:
            with open(self.memory_file, 'w') as f:
                json.dump(self.memory, f, indent=2)
        except Exception as e:
            print(f"Error saving duplicate memory: {e}")
    
    def _clean_old_entries(self):
        """Remove entries older than retention_days."""
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        cutoff_str = cutoff_date.isoformat()
        
        original_count = len(self.memory["articles"])
        self.memory["articles"] = [
            article for article in self.memory["articles"]
            if article.get("timestamp", "") > cutoff_str
        ]
        
        cleaned_count = original_count - len(self.memory["articles"])
        if cleaned_count > 0:
            print(f"Cleaned {cleaned_count} old entries from duplicate memory")
    
    def _generate_content_hash(self, content: str) -> str:
        """Generate a hash for content similarity matching."""
        # Normalize content for hashing
        normalized = re.sub(r'\s+', ' ', content.lower().strip())
        normalized = re.sub(r'[^\w\s]', '', normalized)  # Remove punctuation
        
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def _calculate_similarity(self, content1: str, content2: str) -> float:
        """Calculate similarity between two content strings."""
        # Simple word-based similarity (can be enhanced with embeddings)
        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def _extract_key_features(self, content: str) -> Dict:
        """Extract key features for duplicate detection."""
        # Extract title (first line or sentence)
        lines = content.split('\n')
        title = lines[0] if lines else ""
        
        # Extract first paragraph
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        first_paragraph = paragraphs[0] if paragraphs else ""
        
        return {
            "title": title[:100],  # First 100 chars
            "first_paragraph": first_paragraph[:200],  # First 200 chars
            "content_hash": self._generate_content_hash(content),
            "word_count": len(content.split()),
            "char_count": len(content)
        }
    
    def is_duplicate(self, content: str, url: str = None, similarity_threshold: float = 0.85) -> Tuple[bool, Optional[str]]:
        """
        Check if content is a duplicate of previously seen content.
        Returns (is_duplicate, duplicate_id)
        """
        self._clean_old_entries()
        
        features = self._extract_key_features(content)
        
        for article in self.memory["articles"]:
            # Check exact hash match
            if features["content_hash"] == article["content_hash"]:
                return True, article["id"]
            
            # Check title similarity
            title_similarity = self._calculate_similarity(features["title"], article["title"])
            
            # Check first paragraph similarity
            para_similarity = self._calculate_similarity(features["first_paragraph"], article["first_paragraph"])
            
            # Combined similarity score
            combined_similarity = (title_similarity * 0.6) + (para_similarity * 0.4)
            
            if combined_similarity >= similarity_threshold:
                return True, article["id"]
        
        return False, None
    
    def add_content(self, content: str, url: str = None) -> str:
        """
        Add content to duplicate detection memory.
        Returns the assigned ID for the content.
        """
        self._clean_old_entries()
        
        features = self._extract_key_features(content)
        
        article_id = f"article_{len(self.memory['articles']) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        article_entry = {
            "id": article_id,
            "url": url,
            "timestamp": datetime.now().isoformat(),
            "title": features["title"],
            "first_paragraph": features["first_paragraph"],
            "content_hash": features["content_hash"],
            "word_count": features["word_count"],
            "char_count": features["char_count"]
        }
        
        self.memory["articles"].append(article_entry)
        self._save_memory()
        
        return article_id
    
    def get_stats(self) -> Dict:
        """Get statistics about the duplicate detection memory."""
        self._clean_old_entries()
        
        return {
            "total_articles": len(self.memory["articles"]),
            "retention_days": self.retention_days,
            "oldest_entry": min([a["timestamp"] for a in self.memory["articles"]]) if self.memory["articles"] else None,
            "newest_entry": max([a["timestamp"] for a in self.memory["articles"]]) if self.memory["articles"] else None
        }

# Global instance
duplicate_detector = DuplicateDetector() 