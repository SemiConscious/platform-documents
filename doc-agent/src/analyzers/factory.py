"""
Analyzer factory and language registry.

Provides automatic language detection and analyzer instantiation
for source code analysis across multiple programming languages.
"""

import logging
from pathlib import Path
from typing import Optional, Type

from .base import BaseLanguageAnalyzer
from .models import AnalysisResult

logger = logging.getLogger("doc-agent.analyzers.factory")


# Language detection indicators (filename -> language)
LANGUAGE_INDICATORS: dict[str, str] = {
    # Go
    "go.mod": "go",
    "go.sum": "go",
    # Python
    "requirements.txt": "python",
    "setup.py": "python",
    "pyproject.toml": "python",
    "Pipfile": "python",
    # JavaScript/TypeScript
    "package.json": "javascript",
    "tsconfig.json": "typescript",
    # PHP
    "composer.json": "php",
    # Rust
    "Cargo.toml": "rust",
    # Java
    "pom.xml": "java",
    "build.gradle": "java",
    # Ruby
    "Gemfile": "ruby",
    # Salesforce
    "sfdx-project.json": "apex",
    # C/C++
    "CMakeLists.txt": "cpp",
    "Makefile": "c",  # Could be C or C++
    # Lua
    "init.lua": "lua",
    # ActionScript
    "flex-config.xml": "actionscript",
    # Terraform
    "main.tf": "terraform",
    "variables.tf": "terraform",
    "outputs.tf": "terraform",
    "terraform.tfvars": "terraform",
    ".terraform.lock.hcl": "terraform",
}

# Extension to language mapping
EXTENSION_LANGUAGES: dict[str, str] = {
    ".go": "go",
    ".py": "python",
    ".pyw": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".php": "php",
    ".rs": "rust",
    ".java": "java",
    ".kt": "kotlin",
    ".rb": "ruby",
    ".lua": "lua",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".cxx": "cpp",
    ".cc": "cpp",
    ".hpp": "cpp",
    ".hxx": "cpp",
    ".cs": "csharp",
    ".cls": "apex",
    ".trigger": "apex",
    ".as": "actionscript",
    ".mxml": "actionscript",
    ".sh": "bash",
    ".bash": "bash",
    ".zsh": "bash",
    ".tf": "terraform",
    ".tfvars": "terraform",
    ".hcl": "terraform",
}


class AnalyzerRegistry:
    """Registry of language analyzers."""
    
    _analyzers: dict[str, Type[BaseLanguageAnalyzer]] = {}
    
    @classmethod
    def register(cls, language: str, analyzer_class: Type[BaseLanguageAnalyzer]) -> None:
        """
        Register an analyzer class for a language.
        
        Args:
            language: Language identifier
            analyzer_class: Analyzer class to register
        """
        cls._analyzers[language] = analyzer_class
        logger.debug(f"Registered analyzer for {language}")
    
    @classmethod
    def get(cls, language: str) -> Optional[Type[BaseLanguageAnalyzer]]:
        """
        Get the analyzer class for a language.
        
        Args:
            language: Language identifier
            
        Returns:
            Analyzer class or None if not registered
        """
        return cls._analyzers.get(language)
    
    @classmethod
    def list_languages(cls) -> list[str]:
        """
        List all registered languages.
        
        Returns:
            List of language identifiers
        """
        return list(cls._analyzers.keys())
    
    @classmethod
    def is_registered(cls, language: str) -> bool:
        """
        Check if a language has a registered analyzer.
        
        Args:
            language: Language identifier
            
        Returns:
            True if registered, False otherwise
        """
        return language in cls._analyzers


def register_analyzer(language: str):
    """
    Decorator to register an analyzer class.
    
    Usage:
        @register_analyzer("python")
        class PythonAnalyzer(BaseLanguageAnalyzer):
            ...
    """
    def decorator(cls: Type[BaseLanguageAnalyzer]) -> Type[BaseLanguageAnalyzer]:
        AnalyzerRegistry.register(language, cls)
        return cls
    return decorator


class AnalyzerFactory:
    """
    Factory for creating language analyzers.
    
    Handles language detection and analyzer instantiation.
    """
    
    @staticmethod
    def detect_language(repo_path: Path) -> Optional[str]:
        """
        Detect the primary language of a repository.
        
        Uses indicator files and file extension statistics.
        
        Args:
            repo_path: Path to the repository
            
        Returns:
            Detected language or None
        """
        # Check for indicator files
        for filename, language in LANGUAGE_INDICATORS.items():
            if (repo_path / filename).exists():
                return language
        
        # Count files by extension
        extension_counts: dict[str, int] = {}
        for ext, lang in EXTENSION_LANGUAGES.items():
            count = len(list(repo_path.rglob(f"*{ext}")))
            if count > 0:
                extension_counts[lang] = extension_counts.get(lang, 0) + count
        
        if extension_counts:
            # Return language with most files
            return max(extension_counts.items(), key=lambda x: x[1])[0]
        
        return None
    
    @staticmethod
    def detect_all_languages(repo_path: Path) -> list[str]:
        """
        Detect all languages present in a repository.
        
        Args:
            repo_path: Path to the repository
            
        Returns:
            List of detected languages
        """
        languages = set()
        
        # Check for indicator files
        for filename, language in LANGUAGE_INDICATORS.items():
            if (repo_path / filename).exists():
                languages.add(language)
        
        # Check for files by extension
        for ext, lang in EXTENSION_LANGUAGES.items():
            # Quick check - just see if any files exist
            try:
                next(repo_path.rglob(f"*{ext}"))
                languages.add(lang)
            except StopIteration:
                pass
        
        return list(languages)
    
    @staticmethod
    def get_analyzer(
        repo_path: Path,
        language: Optional[str] = None,
        github_url: Optional[str] = None,
        default_branch: str = "main",
    ) -> Optional[BaseLanguageAnalyzer]:
        """
        Get an analyzer for a repository.
        
        Args:
            repo_path: Path to the repository
            language: Language to analyze (auto-detected if not provided)
            github_url: GitHub URL for source links
            default_branch: Default branch for GitHub links
            
        Returns:
            Analyzer instance or None if language not supported
        """
        if language is None:
            language = AnalyzerFactory.detect_language(repo_path)
        
        if language is None:
            logger.warning(f"Could not detect language for {repo_path}")
            return None
        
        analyzer_class = AnalyzerRegistry.get(language)
        if analyzer_class is None:
            logger.warning(f"No analyzer registered for language: {language}")
            return None
        
        return analyzer_class(
            repo_path=repo_path,
            github_url=github_url,
            default_branch=default_branch,
        )
    
    @staticmethod
    def get_all_analyzers(
        repo_path: Path,
        github_url: Optional[str] = None,
        default_branch: str = "main",
    ) -> list[BaseLanguageAnalyzer]:
        """
        Get analyzers for all detected languages in a repository.
        
        Args:
            repo_path: Path to the repository
            github_url: GitHub URL for source links
            default_branch: Default branch for GitHub links
            
        Returns:
            List of analyzer instances
        """
        languages = AnalyzerFactory.detect_all_languages(repo_path)
        analyzers = []
        
        for language in languages:
            analyzer = AnalyzerFactory.get_analyzer(
                repo_path=repo_path,
                language=language,
                github_url=github_url,
                default_branch=default_branch,
            )
            if analyzer:
                analyzers.append(analyzer)
        
        return analyzers
    
    @staticmethod
    def analyze_repository(
        repo_path: Path,
        github_url: Optional[str] = None,
        default_branch: str = "main",
    ) -> AnalysisResult:
        """
        Analyze a repository using all applicable analyzers.
        
        Args:
            repo_path: Path to the repository
            github_url: GitHub URL for source links
            default_branch: Default branch for GitHub links
            
        Returns:
            Combined AnalysisResult from all analyzers
        """
        analyzers = AnalyzerFactory.get_all_analyzers(
            repo_path=repo_path,
            github_url=github_url,
            default_branch=default_branch,
        )
        
        if not analyzers:
            # Try to detect primary language and create result
            language = AnalyzerFactory.detect_language(repo_path)
            return AnalysisResult(
                language=language or "unknown",
                errors=[f"No analyzer available for language: {language}"] if language else ["Could not detect language"],
            )
        
        # Analyze with each analyzer and merge results
        combined = AnalysisResult(language="")
        for analyzer in analyzers:
            result = analyzer.analyze()
            combined = combined.merge(result)
        
        return combined


# Import and register all language analyzers
def _register_all_analyzers():
    """Import all language analyzer modules to trigger registration."""
    # These imports will trigger the @register_analyzer decorators
    try:
        from .languages import go
    except ImportError:
        pass
    try:
        from .languages import php
    except ImportError:
        pass
    try:
        from .languages import typescript
    except ImportError:
        pass
    try:
        from .languages import python_analyzer
    except ImportError:
        pass
    try:
        from .languages import salesforce
    except ImportError:
        pass
    try:
        from .languages import lua
    except ImportError:
        pass
    try:
        from .languages import rust
    except ImportError:
        pass
    try:
        from .languages import c_cpp
    except ImportError:
        pass
    try:
        from .languages import bash
    except ImportError:
        pass
    try:
        from .languages import actionscript
    except ImportError:
        pass
    try:
        from .languages import terraform
    except ImportError:
        pass


# Register analyzers on module import
_register_all_analyzers()
