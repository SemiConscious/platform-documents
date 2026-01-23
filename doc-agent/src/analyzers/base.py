"""
Base class for language-specific code analyzers.

Each language analyzer extends this base class and implements
the abstract methods for extracting models, endpoints, side effects,
and configuration from source code.
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional

from .models import (
    AnalysisResult,
    ExtractedConfig,
    ExtractedEndpoint,
    ExtractedModel,
    ExtractedSideEffect,
    ExtractedDependency,
)

logger = logging.getLogger("doc-agent.analyzers")


class BaseLanguageAnalyzer(ABC):
    """
    Abstract base class for language-specific code analyzers.
    
    Subclasses must implement methods for extracting:
    - Data models (classes, structs, interfaces, types)
    - API endpoints (routes, handlers, controllers)
    - Side effects (DB queries, HTTP calls, file operations)
    - Configuration (environment variables, config files)
    """
    
    # Class attributes to be overridden by subclasses
    language: str = "unknown"  # tree-sitter language name
    extensions: list[str] = []  # File extensions to analyze
    
    # Directories to exclude from analysis
    EXCLUDE_DIRS = {
        "node_modules", "vendor", ".git", "dist", "build", 
        "__pycache__", ".venv", "venv", ".tox", ".pytest_cache",
        "coverage", ".nyc_output", ".next", ".nuxt",
    }
    
    # Maximum file size to analyze (100KB default)
    MAX_FILE_SIZE = 100 * 1024
    
    def __init__(
        self, 
        repo_path: Path, 
        github_url: Optional[str] = None,
        default_branch: str = "main",
    ):
        """
        Initialize the analyzer.
        
        Args:
            repo_path: Path to the local repository clone
            github_url: GitHub URL for generating source links
            default_branch: Default branch name for GitHub links
        """
        self.repo_path = repo_path
        self.github_url = github_url
        self.default_branch = default_branch
        self.logger = logging.getLogger(f"doc-agent.analyzers.{self.language}")
        self._parser = None
        self._tree_sitter_available = False
        
        # Try to initialize tree-sitter parser
        self._init_parser()
    
    def _init_parser(self) -> None:
        """Initialize the tree-sitter parser for this language."""
        try:
            from tree_sitter_language_pack import get_parser
            self._parser = get_parser(self.language)
            self._tree_sitter_available = True
            self.logger.debug(f"Initialized tree-sitter parser for {self.language}")
        except ImportError:
            self.logger.warning(
                f"tree-sitter-language-pack not available, "
                f"falling back to regex-based parsing for {self.language}"
            )
        except Exception as e:
            self.logger.warning(
                f"Failed to initialize tree-sitter for {self.language}: {e}, "
                f"falling back to regex-based parsing"
            )
    
    def analyze(self) -> AnalysisResult:
        """
        Perform complete code analysis.
        
        Returns:
            AnalysisResult containing all extracted information
        """
        result = AnalysisResult(language=self.language)
        
        try:
            result.models = self.extract_models()
        except Exception as e:
            self.logger.error(f"Error extracting models: {e}")
            result.errors.append(f"Model extraction failed: {str(e)[:100]}")
        
        try:
            result.endpoints = self.extract_endpoints()
        except Exception as e:
            self.logger.error(f"Error extracting endpoints: {e}")
            result.errors.append(f"Endpoint extraction failed: {str(e)[:100]}")
        
        try:
            result.side_effects = self.extract_side_effects()
        except Exception as e:
            self.logger.error(f"Error extracting side effects: {e}")
            result.errors.append(f"Side effect extraction failed: {str(e)[:100]}")
        
        try:
            result.config = self.extract_config()
        except Exception as e:
            self.logger.error(f"Error extracting config: {e}")
            result.errors.append(f"Config extraction failed: {str(e)[:100]}")
        
        try:
            result.dependencies = self.extract_dependencies()
        except Exception as e:
            self.logger.error(f"Error extracting dependencies: {e}")
            result.errors.append(f"Dependency extraction failed: {str(e)[:100]}")
        
        return result
    
    @abstractmethod
    def extract_models(self) -> list[ExtractedModel]:
        """
        Extract data models from source code.
        
        Returns:
            List of extracted models (classes, structs, interfaces, etc.)
        """
        ...
    
    @abstractmethod
    def extract_endpoints(self) -> list[ExtractedEndpoint]:
        """
        Extract API endpoints from source code.
        
        Returns:
            List of extracted endpoints (routes, handlers, etc.)
        """
        ...
    
    @abstractmethod
    def extract_side_effects(self) -> list[ExtractedSideEffect]:
        """
        Extract side effects from source code.
        
        Returns:
            List of extracted side effects (DB queries, HTTP calls, etc.)
        """
        ...
    
    @abstractmethod
    def extract_config(self) -> list[ExtractedConfig]:
        """
        Extract configuration from source code.
        
        Returns:
            List of extracted config items (env vars, config keys, etc.)
        """
        ...
    
    def extract_dependencies(self) -> list[ExtractedDependency]:
        """
        Extract dependencies from source code.
        
        Default implementation returns empty list.
        Override in subclasses for language-specific dependency extraction.
        
        Returns:
            List of extracted dependencies
        """
        return []
    
    # =========================================================================
    # Helper methods for file operations
    # =========================================================================
    
    def find_files(self, patterns: Optional[list[str]] = None) -> list[Path]:
        """
        Find source files matching the analyzer's extensions.
        
        Args:
            patterns: Optional list of glob patterns to match
            
        Returns:
            List of matching file paths
        """
        if patterns is None:
            patterns = [f"*{ext}" for ext in self.extensions]
        
        found = []
        for pattern in patterns:
            # Use rglob for recursive search
            for file_path in self.repo_path.rglob(pattern):
                # Skip excluded directories
                if any(excl in file_path.parts for excl in self.EXCLUDE_DIRS):
                    continue
                
                # Skip non-files and large files
                if not file_path.is_file():
                    continue
                
                try:
                    if file_path.stat().st_size > self.MAX_FILE_SIZE:
                        continue
                except OSError:
                    continue
                
                found.append(file_path)
        
        return found
    
    def read_file(self, path: Path) -> Optional[str]:
        """
        Read a file's contents.
        
        Args:
            path: Path to the file
            
        Returns:
            File contents as string, or None if read fails
        """
        try:
            return path.read_text(errors='ignore')
        except Exception as e:
            self.logger.debug(f"Error reading {path}: {e}")
            return None
    
    def read_file_bytes(self, path: Path) -> Optional[bytes]:
        """
        Read a file's contents as bytes (for tree-sitter).
        
        Args:
            path: Path to the file
            
        Returns:
            File contents as bytes, or None if read fails
        """
        try:
            return path.read_bytes()
        except Exception as e:
            self.logger.debug(f"Error reading {path}: {e}")
            return None
    
    def relative_path(self, path: Path) -> str:
        """
        Get the relative path from the repo root.
        
        Args:
            path: Absolute path to a file
            
        Returns:
            Relative path as string
        """
        try:
            return str(path.relative_to(self.repo_path))
        except ValueError:
            return str(path)
    
    def github_link(self, file: str, line: Optional[int] = None) -> Optional[str]:
        """
        Generate a GitHub link for a file/line.
        
        Args:
            file: Relative file path
            line: Optional line number
            
        Returns:
            GitHub URL or None if no github_url configured
        """
        if not self.github_url:
            return None
        
        url = f"{self.github_url}/blob/{self.default_branch}/{file}"
        if line:
            url = f"{url}#L{line}"
        return url
    
    # =========================================================================
    # Tree-sitter helpers
    # =========================================================================
    
    def parse_file(self, path: Path) -> Optional[Any]:
        """
        Parse a file using tree-sitter.
        
        Args:
            path: Path to the file
            
        Returns:
            Tree-sitter Tree object, or None if parsing fails
        """
        if not self._tree_sitter_available or not self._parser:
            return None
        
        content = self.read_file_bytes(path)
        if content is None:
            return None
        
        try:
            return self._parser.parse(content)
        except Exception as e:
            self.logger.debug(f"Error parsing {path}: {e}")
            return None
    
    def query_tree(self, tree: Any, query_string: str) -> list[tuple[Any, str]]:
        """
        Run a tree-sitter query on a parsed tree.
        
        Args:
            tree: Tree-sitter Tree object
            query_string: Tree-sitter query string
            
        Returns:
            List of (node, capture_name) tuples
        """
        if not self._tree_sitter_available or not self._parser:
            return []
        
        try:
            from tree_sitter_language_pack import get_language
            language = get_language(self.language)
            query = language.query(query_string)
            return query.captures(tree.root_node)
        except Exception as e:
            self.logger.debug(f"Query error: {e}")
            return []
    
    def get_node_text(self, node: Any, content: bytes) -> str:
        """
        Get the text content of a tree-sitter node.
        
        Args:
            node: Tree-sitter Node object
            content: Original file content as bytes
            
        Returns:
            Node text as string
        """
        try:
            return content[node.start_byte:node.end_byte].decode('utf-8', errors='ignore')
        except Exception:
            return ""
    
    def get_node_line(self, node: Any) -> int:
        """
        Get the line number of a tree-sitter node.
        
        Args:
            node: Tree-sitter Node object
            
        Returns:
            1-based line number
        """
        try:
            return node.start_point[0] + 1  # tree-sitter uses 0-based
        except Exception:
            return 0
