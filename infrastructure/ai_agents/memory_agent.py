"""
MemAgent - Persistent Memory System for AI Agents
Letta-style memory management for news classification agents
"""

import hashlib
import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class MemoryEntry:
    """Individual memory entry with content and metadata"""

    id: str
    agent_id: str
    content: str
    memory_type: str  # "fact", "pattern", "context", "preference"
    relevance_score: float  # 0.0-1.0
    access_count: int
    created_at: datetime
    last_accessed: datetime
    expires_at: Optional[datetime] = None
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class MemAgent:
    """
    Persistent memory system for AI agents with Letta-style capabilities

    Features:
    - Long-term memory storage across sessions
    - Memory relevance scoring and retrieval
    - Context-aware memory management
    - Agent-specific memory isolation
    - Memory decay and cleanup
    """

    def __init__(self, db_path: str = "infrastructure/ai_agents/agent_memory.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database for memory storage"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    memory_type TEXT NOT NULL,
                    relevance_score REAL NOT NULL,
                    access_count INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    last_accessed TEXT NOT NULL,
                    expires_at TEXT,
                    tags TEXT
                )
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_agent_type 
                ON memories(agent_id, memory_type)
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_relevance 
                ON memories(relevance_score DESC)
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_last_accessed 
                ON memories(last_accessed DESC)
            """
            )

    def store_memory(
        self,
        agent_id: str,
        content: str,
        memory_type: str,
        relevance_score: float = 0.5,
        tags: List[str] = None,
        expires_in_days: Optional[int] = None,
    ) -> str:
        """Store a new memory entry"""
        memory_id = hashlib.md5(f"{agent_id}_{content}_{datetime.now().isoformat()}".encode()).hexdigest()

        now = datetime.now()
        expires_at = now + timedelta(days=expires_in_days) if expires_in_days else None

        memory = MemoryEntry(
            id=memory_id,
            agent_id=agent_id,
            content=content,
            memory_type=memory_type,
            relevance_score=max(0.0, min(1.0, relevance_score)),
            access_count=0,
            created_at=now,
            last_accessed=now,
            expires_at=expires_at,
            tags=tags or [],
        )

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO memories 
                (id, agent_id, content, memory_type, relevance_score, 
                 access_count, created_at, last_accessed, expires_at, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    memory.id,
                    memory.agent_id,
                    memory.content,
                    memory.memory_type,
                    memory.relevance_score,
                    memory.access_count,
                    memory.created_at.isoformat(),
                    memory.last_accessed.isoformat(),
                    memory.expires_at.isoformat() if memory.expires_at else None,
                    json.dumps(memory.tags),
                ),
            )

        return memory_id

    def retrieve_memories(
        self,
        agent_id: str,
        memory_type: Optional[str] = None,
        limit: int = 10,
        min_relevance: float = 0.1,
    ) -> List[MemoryEntry]:
        """Retrieve relevant memories for an agent"""
        query = """
            SELECT * FROM memories 
            WHERE agent_id = ? AND relevance_score >= ?
            AND (expires_at IS NULL OR expires_at > ?)
        """
        params = [agent_id, min_relevance, datetime.now().isoformat()]

        if memory_type:
            query += " AND memory_type = ?"
            params.append(memory_type)

        query += " ORDER BY relevance_score DESC, last_accessed DESC LIMIT ?"
        params.append(limit)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

        memories = []
        for row in rows:
            memory = MemoryEntry(
                id=row[0],
                agent_id=row[1],
                content=row[2],
                memory_type=row[3],
                relevance_score=row[4],
                access_count=row[5],
                created_at=datetime.fromisoformat(row[6]),
                last_accessed=datetime.fromisoformat(row[7]),
                expires_at=datetime.fromisoformat(row[8]) if row[8] else None,
                tags=json.loads(row[9]) if row[9] else [],
            )
            memories.append(memory)

            # Update access count and timestamp
            self._update_access(memory.id)

        return memories

    def _update_access(self, memory_id: str):
        """Update access count and timestamp for a memory"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE memories 
                SET access_count = access_count + 1, last_accessed = ?
                WHERE id = ?
            """,
                (datetime.now().isoformat(), memory_id),
            )

    def search_memories(self, agent_id: str, query: str, limit: int = 5) -> List[MemoryEntry]:
        """Search memories by content similarity"""
        memories = self.retrieve_memories(agent_id, limit=100)

        # Simple text similarity search (can be enhanced with embeddings)
        query_words = set(query.lower().split())
        scored_memories = []

        for memory in memories:
            content_words = set(memory.content.lower().split())
            similarity = len(query_words.intersection(content_words)) / len(query_words.union(content_words))
            if similarity > 0.1:  # Minimum similarity threshold
                scored_memories.append((memory, similarity))

        # Sort by similarity score
        scored_memories.sort(key=lambda x: x[1], reverse=True)
        return [memory for memory, _ in scored_memories[:limit]]

    def update_relevance(self, memory_id: str, new_relevance: float):
        """Update relevance score of a memory"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE memories 
                SET relevance_score = ?
                WHERE id = ?
            """,
                (max(0.0, min(1.0, new_relevance)), memory_id),
            )

    def cleanup_expired_memories(self):
        """Remove expired memories"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                DELETE FROM memories 
                WHERE expires_at IS NOT NULL AND expires_at < ?
            """,
                (datetime.now().isoformat(),),
            )
            return cursor.rowcount

    def get_agent_memory_stats(self, agent_id: str) -> Dict[str, Any]:
        """Get memory statistics for an agent"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT 
                    COUNT(*) as total_memories,
                    AVG(relevance_score) as avg_relevance,
                    SUM(access_count) as total_accesses,
                    memory_type,
                    COUNT(*) as type_count
                FROM memories 
                WHERE agent_id = ?
                GROUP BY memory_type
            """,
                (agent_id,),
            )

            type_stats = {}
            total_memories = 0
            total_accesses = 0
            relevance_sum = 0

            for row in cursor.fetchall():
                if row[3]:  # memory_type exists
                    type_stats[row[3]] = row[4]  # type_count
                    total_memories += row[4]
                    total_accesses += row[2] if row[2] else 0
                    relevance_sum += (row[1] or 0) * row[4]

            avg_relevance = relevance_sum / total_memories if total_memories > 0 else 0

            return {
                "total_memories": total_memories,
                "average_relevance": avg_relevance,
                "total_accesses": total_accesses,
                "memory_types": type_stats,
                "agent_id": agent_id,
            }


# Global memory agent instance
memory_agent = MemAgent()


def get_memory_agent() -> MemAgent:
    """Get the global memory agent instance"""
    return memory_agent
