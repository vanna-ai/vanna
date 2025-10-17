"""
Local vector database implementation of AgentMemory.

This implementation uses ChromaDB for local vector storage of tool usage patterns.
"""

import json
import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

from vanna.capabilities.agent_memory import AgentMemory, ToolMemory, MemorySearchResult
from vanna.core.tool import ToolContext


class ChromaAgentMemory(AgentMemory):
    """ChromaDB-based implementation of AgentMemory."""
    
    def __init__(
        self,
        persist_directory: str = "./chroma_memory",
        collection_name: str = "tool_memories",
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    ):
        if not CHROMADB_AVAILABLE:
            raise ImportError("ChromaDB is required for ChromaAgentMemory. Install with: pip install chromadb")
        
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        self._client = None
        self._collection = None
        self._executor = ThreadPoolExecutor(max_workers=2)
    
    def _get_client(self):
        """Get or create ChromaDB client."""
        if self._client is None:
            self._client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
        return self._client
    
    def _get_collection(self):
        """Get or create ChromaDB collection."""
        if self._collection is None:
            client = self._get_client()
            try:
                self._collection = client.get_collection(name=self.collection_name)
            except Exception:
                self._collection = client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "Tool usage memories for learning"}
                )
        return self._collection
    
    def _create_memory_id(self, question: str, tool_name: str, args: Dict[str, Any]) -> str:
        """Create a unique ID for a memory."""
        content = f"{question}|{tool_name}|{json.dumps(args, sort_keys=True)}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def save_tool_usage(
        self,
        question: str,
        tool_name: str,
        args: Dict[str, Any],
        context: ToolContext,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Save a tool usage pattern."""
        def _save():
            collection = self._get_collection()
            
            memory_id = self._create_memory_id(question, tool_name, args)
            timestamp = datetime.now().isoformat()
            
            memory_data = {
                "question": question,
                "tool_name": tool_name,
                "args": args,
                "timestamp": timestamp,
                "success": success,
                "metadata": metadata or {}
            }
            
            # Use question as document text for embedding
            collection.upsert(
                ids=[memory_id],
                documents=[question],
                metadatas=[memory_data]
            )
        
        await asyncio.get_event_loop().run_in_executor(self._executor, _save)
    
    async def search_similar_usage(
        self,
        question: str,
        context: ToolContext,
        *,
        limit: int = 10,
        similarity_threshold: float = 0.7,
        tool_name_filter: Optional[str] = None
    ) -> List[MemorySearchResult]:
        """Search for similar tool usage patterns."""
        def _search():
            collection = self._get_collection()
            
            # Prepare where filter
            where_filter = {"success": True}  # Only successful usage patterns
            if tool_name_filter:
                where_filter["tool_name"] = tool_name_filter
            
            results = collection.query(
                query_texts=[question],
                n_results=limit,
                where=where_filter
            )
            
            search_results = []
            if results["ids"] and len(results["ids"][0]) > 0:
                for i, (id_, distance, metadata) in enumerate(zip(
                    results["ids"][0],
                    results["distances"][0],
                    results["metadatas"][0]
                )):
                    # Convert distance to similarity score (ChromaDB uses L2 distance)
                    similarity_score = max(0, 1 - distance)
                    
                    if similarity_score >= similarity_threshold:
                        memory = ToolMemory(
                            question=metadata["question"],
                            tool_name=metadata["tool_name"],
                            args=metadata["args"],
                            timestamp=metadata.get("timestamp"),
                            success=metadata.get("success", True),
                            metadata=metadata.get("metadata", {})
                        )
                        
                        search_results.append(MemorySearchResult(
                            memory=memory,
                            similarity_score=similarity_score,
                            rank=i + 1
                        ))
            
            return search_results
        
        return await asyncio.get_event_loop().run_in_executor(self._executor, _search)
    
    async def get_tool_usage_stats(
        self,
        context: ToolContext,
        tool_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get usage statistics."""
        def _get_stats():
            collection = self._get_collection()
            
            # Get all memories
            where_filter = {}
            if tool_name:
                where_filter["tool_name"] = tool_name
            
            results = collection.get(where=where_filter if where_filter else None)
            
            if not results["metadatas"]:
                return {
                    "total_memories": 0,
                    "unique_tools": 0,
                    "unique_questions": 0,
                    "success_rate": 0.0,
                    "most_used_tools": {}
                }
            
            metadatas = results["metadatas"]
            total_memories = len(metadatas)
            
            unique_tools = set()
            unique_questions = set()
            tool_counts = {}
            successful_count = 0
            
            for metadata in metadatas:
                tool = metadata["tool_name"]
                question = metadata["question"]
                success = metadata.get("success", True)
                
                unique_tools.add(tool)
                unique_questions.add(question)
                tool_counts[tool] = tool_counts.get(tool, 0) + 1
                
                if success:
                    successful_count += 1
            
            success_rate = successful_count / total_memories if total_memories > 0 else 0.0
            
            # Sort tools by usage count
            most_used_tools = dict(sorted(tool_counts.items(), key=lambda x: x[1], reverse=True))
            
            return {
                "total_memories": total_memories,
                "unique_tools": len(unique_tools),
                "unique_questions": len(unique_questions),
                "success_rate": success_rate,
                "most_used_tools": most_used_tools
            }
        
        return await asyncio.get_event_loop().run_in_executor(self._executor, _get_stats)
    
    async def clear_memories(
        self,
        context: ToolContext,
        tool_name: Optional[str] = None,
        before_date: Optional[str] = None
    ) -> int:
        """Clear stored memories."""
        def _clear():
            collection = self._get_collection()
            
            # Build where filter
            where_filter = {}
            if tool_name:
                where_filter["tool_name"] = tool_name
            
            # Get memories to delete
            results = collection.get(where=where_filter if where_filter else None)
            
            if not results["ids"]:
                return 0
            
            ids_to_delete = []
            for i, metadata in enumerate(results["metadatas"]):
                if before_date:
                    memory_date = metadata.get("timestamp", "")
                    if memory_date and memory_date < before_date:
                        ids_to_delete.append(results["ids"][i])
                else:
                    ids_to_delete.append(results["ids"][i])
            
            if ids_to_delete:
                collection.delete(ids=ids_to_delete)
            
            return len(ids_to_delete)
        
        return await asyncio.get_event_loop().run_in_executor(self._executor, _clear)
    
    async def list_tools_with_memories(
        self,
        context: ToolContext
    ) -> List[str]:
        """List all tool names that have stored memories."""
        def _list_tools():
            collection = self._get_collection()
            
            results = collection.get()
            
            if not results["metadatas"]:
                return []
            
            unique_tools = set()
            for metadata in results["metadatas"]:
                unique_tools.add(metadata["tool_name"])
            
            return sorted(list(unique_tools))
        
        return await asyncio.get_event_loop().run_in_executor(self._executor, _list_tools)