"""
File Store for context size management.

When tool responses exceed a threshold, the content is stored here and
replaced with a lightweight reference. The LLM can retrieve the content
(whole, chunked, or summary) using the FileStoreTool.
"""

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from enum import Enum

logger = logging.getLogger("doc-agent.context.file_store")

# Content larger than this will be stored in the file store
STORAGE_THRESHOLD_BYTES = 1024  # 1KB


class ContentType(str, Enum):
    """Types of content that can be stored."""
    TEXT = "text"
    JSON = "json"
    MARKDOWN = "markdown"
    CODE = "code"
    UNKNOWN = "unknown"


@dataclass
class FileReference:
    """
    Lightweight reference to content stored in the file store.
    
    This replaces the actual content in conversation history to save context space.
    Contains enough metadata for the LLM to decide if it needs the full content.
    """
    ref_id: str
    size_bytes: int
    content_type: ContentType
    preview: str  # First ~200 chars
    summary: Optional[str] = None  # AI-generated summary
    created_at: datetime = field(default_factory=datetime.utcnow)
    source: Optional[str] = None  # What tool/agent created this
    
    def to_context_string(self) -> str:
        """
        Format the reference for inclusion in conversation context.
        
        This is what the LLM sees instead of the full content.
        """
        lines = [
            f"[FileStore Reference: {self.ref_id}]",
            f"Size: {self._format_size(self.size_bytes)}",
            f"Type: {self.content_type.value}",
        ]
        
        if self.summary:
            lines.append(f"Summary: {self.summary}")
        
        lines.append(f"Preview: {self.preview}...")
        lines.append(f"Use file_store_read(ref_id='{self.ref_id}') to retrieve content.")
        
        return "\n".join(lines)
    
    def _format_size(self, size: int) -> str:
        """Format byte size for human reading."""
        if size < 1024:
            return f"{size} bytes"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size / (1024 * 1024):.1f} MB"
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "ref_id": self.ref_id,
            "size_bytes": self.size_bytes,
            "content_type": self.content_type.value,
            "preview": self.preview,
            "summary": self.summary,
            "created_at": self.created_at.isoformat(),
            "source": self.source,
        }


@dataclass
class StoredFile:
    """Internal representation of a stored file."""
    ref_id: str
    content: str
    reference: FileReference


class FileStore:
    """
    In-memory store for large content that would bloat conversation context.
    
    Usage:
        store = FileStore()
        
        # Store content (returns reference if over threshold, else original)
        result = store.store_if_large(content, source="repo_scanner")
        
        # Retrieve content
        content = store.read(ref_id)
        chunk = store.read_chunk(ref_id, start=0, end=4096)
        summary = store.get_summary(ref_id)
    """
    
    def __init__(self, threshold_bytes: int = STORAGE_THRESHOLD_BYTES):
        """
        Initialize the file store.
        
        Args:
            threshold_bytes: Content larger than this will be stored
        """
        self.threshold = threshold_bytes
        self._files: dict[str, StoredFile] = {}
        self._summary_generator: Optional[callable] = None
    
    def set_summary_generator(self, generator: callable) -> None:
        """
        Set a function to generate summaries for stored content.
        
        Args:
            generator: Async function(content: str) -> str that generates summaries
        """
        self._summary_generator = generator
    
    def store_if_large(
        self,
        content: str,
        source: Optional[str] = None,
        content_type: Optional[ContentType] = None,
        force_store: bool = False,
    ) -> str | FileReference:
        """
        Store content if it exceeds the threshold.
        
        Args:
            content: The content to potentially store
            source: What created this content (for metadata)
            content_type: Type of content (auto-detected if not provided)
            force_store: Store regardless of size
            
        Returns:
            Original content if under threshold, FileReference if stored
        """
        size = len(content.encode('utf-8'))
        
        if not force_store and size <= self.threshold:
            return content
        
        # Generate reference ID
        ref_id = self._generate_ref_id(content)
        
        # Detect content type if not provided
        if content_type is None:
            content_type = self._detect_content_type(content)
        
        # Generate preview (first ~200 chars, clean)
        preview = self._generate_preview(content)
        
        # Create reference
        reference = FileReference(
            ref_id=ref_id,
            size_bytes=size,
            content_type=content_type,
            preview=preview,
            source=source,
        )
        
        # Store the file
        self._files[ref_id] = StoredFile(
            ref_id=ref_id,
            content=content,
            reference=reference,
        )
        
        logger.debug(f"Stored {size} bytes with ref_id={ref_id}")
        
        return reference
    
    async def store_if_large_async(
        self,
        content: str,
        source: Optional[str] = None,
        content_type: Optional[ContentType] = None,
        force_store: bool = False,
        generate_summary: bool = True,
    ) -> str | FileReference:
        """
        Store content if it exceeds the threshold, with async summary generation.
        
        Args:
            content: The content to potentially store
            source: What created this content
            content_type: Type of content
            force_store: Store regardless of size
            generate_summary: Whether to generate an AI summary
            
        Returns:
            Original content if under threshold, FileReference if stored
        """
        result = self.store_if_large(content, source, content_type, force_store)
        
        if isinstance(result, FileReference) and generate_summary and self._summary_generator:
            try:
                summary = await self._summary_generator(content)
                result.summary = summary
                self._files[result.ref_id].reference.summary = summary
            except Exception as e:
                logger.warning(f"Failed to generate summary: {e}")
        
        return result
    
    def read(self, ref_id: str) -> Optional[str]:
        """
        Read the full content of a stored file.
        
        Args:
            ref_id: The reference ID
            
        Returns:
            The content or None if not found
        """
        stored = self._files.get(ref_id)
        if stored:
            return stored.content
        return None
    
    def read_chunk(
        self,
        ref_id: str,
        start: int = 0,
        end: Optional[int] = None,
    ) -> Optional[str]:
        """
        Read a byte range from a stored file.
        
        Args:
            ref_id: The reference ID
            start: Start byte offset (inclusive)
            end: End byte offset (exclusive), None for end of file
            
        Returns:
            The chunk content or None if not found
        """
        stored = self._files.get(ref_id)
        if not stored:
            return None
        
        content_bytes = stored.content.encode('utf-8')
        
        if end is None:
            end = len(content_bytes)
        
        # Clamp to valid range
        start = max(0, min(start, len(content_bytes)))
        end = max(start, min(end, len(content_bytes)))
        
        chunk_bytes = content_bytes[start:end]
        
        # Decode, handling partial UTF-8 characters at boundaries
        try:
            return chunk_bytes.decode('utf-8')
        except UnicodeDecodeError:
            # Try to find valid UTF-8 boundaries
            return chunk_bytes.decode('utf-8', errors='ignore')
    
    def get_reference(self, ref_id: str) -> Optional[FileReference]:
        """Get the reference metadata for a stored file."""
        stored = self._files.get(ref_id)
        if stored:
            return stored.reference
        return None
    
    def get_summary(self, ref_id: str) -> Optional[str]:
        """Get just the summary for a stored file."""
        stored = self._files.get(ref_id)
        if stored and stored.reference.summary:
            return stored.reference.summary
        return None
    
    def list_files(self) -> list[FileReference]:
        """List all stored file references."""
        return [f.reference for f in self._files.values()]
    
    def delete(self, ref_id: str) -> bool:
        """Delete a stored file."""
        if ref_id in self._files:
            del self._files[ref_id]
            return True
        return False
    
    def clear(self) -> None:
        """Clear all stored files."""
        self._files.clear()
    
    def get_stats(self) -> dict[str, Any]:
        """Get statistics about the file store."""
        total_size = sum(f.reference.size_bytes for f in self._files.values())
        return {
            "file_count": len(self._files),
            "total_size_bytes": total_size,
            "threshold_bytes": self.threshold,
        }
    
    def _generate_ref_id(self, content: str) -> str:
        """Generate a unique reference ID for content."""
        # Use first 12 chars of SHA256 hash
        hash_input = f"{datetime.utcnow().isoformat()}{content[:1000]}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:12]
    
    def _detect_content_type(self, content: str) -> ContentType:
        """Auto-detect content type from content."""
        content_start = content[:500].lower()
        
        if content.strip().startswith('{') or content.strip().startswith('['):
            return ContentType.JSON
        elif content_start.startswith('# ') or '\n## ' in content:
            return ContentType.MARKDOWN
        elif any(kw in content_start for kw in ['def ', 'class ', 'import ', 'function ', 'const ', 'var ']):
            return ContentType.CODE
        else:
            return ContentType.TEXT
    
    def _generate_preview(self, content: str, max_length: int = 200) -> str:
        """Generate a preview of the content."""
        # Clean up whitespace
        preview = ' '.join(content.split())
        
        if len(preview) <= max_length:
            return preview
        
        # Truncate at word boundary
        truncated = preview[:max_length]
        last_space = truncated.rfind(' ')
        if last_space > max_length * 0.7:
            truncated = truncated[:last_space]
        
        return truncated


class FileStoreTool:
    """
    Tool interface for the LLM to interact with the file store.
    
    This provides the schema and handler for the file_store_read tool.
    """
    
    def __init__(self, file_store: FileStore):
        self.store = file_store
    
    @property
    def tool_definition(self) -> dict[str, Any]:
        """
        Get the tool definition for Claude's tool use.
        """
        return {
            "name": "file_store_read",
            "description": (
                "Read content from the file store. Use this to retrieve full content "
                "that was summarized in previous tool responses. You can read the full "
                "file, a specific byte range (chunk), or just the summary."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "ref_id": {
                        "type": "string",
                        "description": "The reference ID of the file to read",
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["full", "chunk", "summary", "info"],
                        "description": (
                            "What to read: 'full' for entire content, 'chunk' for byte range, "
                            "'summary' for AI summary only, 'info' for metadata"
                        ),
                        "default": "full",
                    },
                    "start": {
                        "type": "integer",
                        "description": "Start byte offset for chunk mode (default 0)",
                        "default": 0,
                    },
                    "end": {
                        "type": "integer",
                        "description": "End byte offset for chunk mode (default: end of file)",
                    },
                },
                "required": ["ref_id"],
            },
        }
    
    def handle(
        self,
        ref_id: str,
        mode: str = "full",
        start: int = 0,
        end: Optional[int] = None,
    ) -> dict[str, Any]:
        """
        Handle a file_store_read tool call.
        
        Args:
            ref_id: The file reference ID
            mode: Read mode (full, chunk, summary, info)
            start: Start byte for chunk mode
            end: End byte for chunk mode
            
        Returns:
            Tool response dictionary
        """
        reference = self.store.get_reference(ref_id)
        
        if not reference:
            return {
                "success": False,
                "error": f"File not found: {ref_id}",
            }
        
        if mode == "info":
            return {
                "success": True,
                "ref_id": ref_id,
                "size_bytes": reference.size_bytes,
                "content_type": reference.content_type.value,
                "preview": reference.preview,
                "summary": reference.summary,
                "source": reference.source,
            }
        
        if mode == "summary":
            summary = self.store.get_summary(ref_id)
            if summary:
                return {
                    "success": True,
                    "ref_id": ref_id,
                    "summary": summary,
                }
            else:
                return {
                    "success": False,
                    "error": "No summary available for this file",
                    "ref_id": ref_id,
                }
        
        if mode == "chunk":
            content = self.store.read_chunk(ref_id, start, end)
            actual_end = end if end else reference.size_bytes
            return {
                "success": True,
                "ref_id": ref_id,
                "mode": "chunk",
                "start": start,
                "end": actual_end,
                "total_size": reference.size_bytes,
                "content": content,
            }
        
        # mode == "full"
        content = self.store.read(ref_id)
        return {
            "success": True,
            "ref_id": ref_id,
            "mode": "full",
            "size_bytes": reference.size_bytes,
            "content": content,
        }
    
    def list_files(self) -> dict[str, Any]:
        """
        List all files in the store (can be exposed as separate tool if needed).
        """
        files = self.store.list_files()
        return {
            "success": True,
            "count": len(files),
            "files": [
                {
                    "ref_id": f.ref_id,
                    "size_bytes": f.size_bytes,
                    "content_type": f.content_type.value,
                    "preview": f.preview,
                    "summary": f.summary,
                    "source": f.source,
                }
                for f in files
            ],
        }
