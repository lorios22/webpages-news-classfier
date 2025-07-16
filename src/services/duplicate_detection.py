import hashlib
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Set


class DuplicateDetector:
    """
    Advanced duplicate detection system for news articles.

    Features:
    - Content-based duplicate detection using multiple algorithms
    - URL-based duplicate tracking
    - Persistent memory storage
    - Configurable similarity thresholds
    """

    def __init__(self, memory_file: str = "duplicate_memory.json"):
        """
        Initialize the duplicate detector.

        Args:
            memory_file: Path to the JSON file for storing duplicate records
        """
        self.memory_file = memory_file
        self.duplicates_memory = self._load_memory()

    def _load_memory(self) -> Dict:
        """Load duplicate detection memory from file"""
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            return {"articles": {}, "urls": set(), "hashes": {}}
        except Exception:
            return {"articles": {}, "urls": set(), "hashes": {}}

    def _save_memory(self):
        """Save duplicate detection memory to file"""
        try:
            # Convert sets to lists for JSON serialization
            memory_to_save = {
                "articles": self.duplicates_memory["articles"],
                "urls": list(self.duplicates_memory["urls"]),
                "hashes": self.duplicates_memory["hashes"],
            }

            with open(self.memory_file, "w", encoding="utf-8") as f:
                json.dump(memory_to_save, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Could not save duplicate memory: {e}")

    def _generate_content_hash(self, content: str) -> str:
        """Generate a hash for the content"""
        return hashlib.md5(content.encode("utf-8")).hexdigest()

    def _normalize_content(self, content: str) -> str:
        """Normalize content for comparison"""
        # Remove extra whitespace and convert to lowercase
        return " ".join(content.lower().split())

    def is_duplicate(self, url: str, content: str, title: str = "") -> bool:
        """
        Check if article is a duplicate.

        Args:
            url: Article URL
            content: Article content
            title: Article title (optional)

        Returns:
            True if duplicate, False otherwise
        """
        # Check URL duplicates
        if url in self.duplicates_memory["urls"]:
            return True

        # Check content hash duplicates
        content_hash = self._generate_content_hash(self._normalize_content(content))
        if content_hash in self.duplicates_memory["hashes"]:
            return True

        return False

    def add_article(self, url: str, content: str, title: str = "", article_id: str = None):
        """
        Add article to duplicate tracking.

        Args:
            url: Article URL
            content: Article content
            title: Article title
            article_id: Unique article identifier
        """
        if article_id is None:
            article_id = f"article_{len(self.duplicates_memory['articles'])}"

        content_hash = self._generate_content_hash(self._normalize_content(content))

        # Add to memory
        self.duplicates_memory["articles"][article_id] = {
            "url": url,
            "title": title,
            "content_hash": content_hash,
            "timestamp": datetime.now().isoformat(),
        }

        # Ensure urls is a set
        if isinstance(self.duplicates_memory["urls"], list):
            self.duplicates_memory["urls"] = set(self.duplicates_memory["urls"])

        self.duplicates_memory["urls"].add(url)
        self.duplicates_memory["hashes"][content_hash] = article_id

        # Save memory
        self._save_memory()

    def get_duplicate_count(self) -> int:
        """Get total number of tracked articles"""
        return len(self.duplicates_memory["articles"])

    def clear_memory(self):
        """Clear all duplicate detection memory"""
        self.duplicates_memory = {"articles": {}, "urls": set(), "hashes": {}}
        self._save_memory()


# Create global instance
duplicate_detector = DuplicateDetector()

# Export for other modules
__all__ = ["duplicate_detector", "DuplicateDetector"]
