"""Route extractor for extracting API routes from source code."""

import re
import logging
from dataclasses import dataclass, field
from typing import Optional, Any
from enum import Enum

logger = logging.getLogger("doc-agent.parsers.routes")


class HTTPMethod(str, Enum):
    """HTTP methods."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    OPTIONS = "OPTIONS"
    HEAD = "HEAD"
    ALL = "ALL"


class Framework(str, Enum):
    """Supported frameworks."""
    EXPRESS = "express"
    FASTIFY = "fastify"
    KOA = "koa"
    FASTAPI = "fastapi"
    FLASK = "flask"
    DJANGO = "django"
    GIN = "gin"
    GORILLA = "gorilla"
    CHI = "chi"
    FIBER = "fiber"
    UNKNOWN = "unknown"


@dataclass
class ExtractedRoute:
    """A route extracted from source code."""
    path: str
    method: HTTPMethod
    handler_name: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    middleware: list[str] = field(default_factory=list)
    description: Optional[str] = None
    framework: Framework = Framework.UNKNOWN
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "method": self.method.value,
            "handler_name": self.handler_name,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "middleware": self.middleware,
            "description": self.description,
            "framework": self.framework.value,
        }


class RouteExtractor:
    """
    Extracts API routes from source code for various frameworks.
    
    Supports:
    - Express.js / Fastify / Koa (JavaScript/TypeScript)
    - FastAPI / Flask / Django (Python)
    - Gin / Gorilla Mux / Chi / Fiber (Go)
    """
    
    def __init__(self):
        self.routes: list[ExtractedRoute] = []
    
    def extract(
        self,
        content: str,
        file_path: str,
        language: Optional[str] = None,
    ) -> list[ExtractedRoute]:
        """
        Extract routes from source code.
        
        Args:
            content: Source code content
            file_path: Path to the source file
            language: Programming language (auto-detected if not provided)
            
        Returns:
            List of extracted routes
        """
        if language is None:
            language = self._detect_language(file_path)
        
        self.routes = []
        
        if language in ("javascript", "typescript"):
            self._extract_js_routes(content, file_path)
        elif language == "python":
            self._extract_python_routes(content, file_path)
        elif language == "go":
            self._extract_go_routes(content, file_path)
        
        logger.debug(f"Extracted {len(self.routes)} routes from {file_path}")
        return self.routes
    
    def extract_multiple(
        self,
        files: list[tuple[str, str, Optional[str]]],  # (content, path, language)
    ) -> list[ExtractedRoute]:
        """Extract routes from multiple files."""
        all_routes = []
        for content, path, lang in files:
            routes = self.extract(content, path, lang)
            all_routes.extend(routes)
        return all_routes
    
    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension."""
        ext = file_path.rsplit(".", 1)[-1].lower()
        
        language_map = {
            "js": "javascript",
            "mjs": "javascript",
            "cjs": "javascript",
            "ts": "typescript",
            "tsx": "typescript",
            "py": "python",
            "go": "go",
        }
        
        return language_map.get(ext, "unknown")
    
    # ==================== JavaScript/TypeScript ====================
    
    def _extract_js_routes(self, content: str, file_path: str) -> None:
        """Extract routes from JavaScript/TypeScript code."""
        # Detect framework
        framework = self._detect_js_framework(content)
        
        if framework in (Framework.EXPRESS, Framework.FASTIFY):
            self._extract_express_routes(content, file_path, framework)
        elif framework == Framework.KOA:
            self._extract_koa_routes(content, file_path)
    
    def _detect_js_framework(self, content: str) -> Framework:
        """Detect JavaScript framework from imports/requires."""
        if re.search(r"require\(['\"]express['\"]\)|from ['\"]express['\"]", content):
            return Framework.EXPRESS
        if re.search(r"require\(['\"]fastify['\"]\)|from ['\"]fastify['\"]", content):
            return Framework.FASTIFY
        if re.search(r"require\(['\"]@?koa['\"]\)|from ['\"]@?koa['\"]", content):
            return Framework.KOA
        return Framework.EXPRESS  # Default assumption
    
    def _extract_express_routes(
        self,
        content: str,
        file_path: str,
        framework: Framework,
    ) -> None:
        """Extract routes from Express.js or Fastify code."""
        # Pattern for route definitions
        # Matches: app.get('/path', handler), router.post('/api/users', middleware, handler)
        patterns = [
            # Standard route methods
            re.compile(
                r'(?:app|router|server)\s*\.\s*(get|post|put|patch|delete|options|head|all)\s*\(\s*'
                r'[\'"`]([^\'"`]+)[\'"`]'  # Path
                r'(?:\s*,\s*[^)]+)?'  # Optional middleware/handler
                r'\)',
                re.IGNORECASE | re.MULTILINE
            ),
            # Route method chaining
            re.compile(
                r'\.route\s*\(\s*[\'"`]([^\'"`]+)[\'"`]\s*\)'
                r'\s*\.\s*(get|post|put|patch|delete|options|head)\s*\(',
                re.IGNORECASE | re.MULTILINE
            ),
        ]
        
        lines = content.split("\n")
        
        for pattern in patterns:
            for match in pattern.finditer(content):
                if pattern.pattern.startswith(r'\.route'):
                    path = match.group(1)
                    method = match.group(2).upper()
                else:
                    method = match.group(1).upper()
                    path = match.group(2)
                
                # Find line number
                line_num = content[:match.start()].count("\n") + 1
                
                # Extract handler name if possible
                handler = self._extract_js_handler_name(content, match.end())
                
                # Look for comments above the route
                description = self._extract_js_comment(lines, line_num - 1)
                
                self.routes.append(ExtractedRoute(
                    path=path,
                    method=HTTPMethod(method),
                    handler_name=handler,
                    file_path=file_path,
                    line_number=line_num,
                    description=description,
                    framework=framework,
                ))
    
    def _extract_koa_routes(self, content: str, file_path: str) -> None:
        """Extract routes from Koa.js code (with koa-router)."""
        pattern = re.compile(
            r'router\s*\.\s*(get|post|put|patch|delete|options|head|all)\s*\(\s*'
            r'[\'"`]([^\'"`]+)[\'"`]',
            re.IGNORECASE | re.MULTILINE
        )
        
        for match in pattern.finditer(content):
            method = match.group(1).upper()
            path = match.group(2)
            line_num = content[:match.start()].count("\n") + 1
            
            self.routes.append(ExtractedRoute(
                path=path,
                method=HTTPMethod(method),
                file_path=file_path,
                line_number=line_num,
                framework=Framework.KOA,
            ))
    
    def _extract_js_handler_name(self, content: str, start_pos: int) -> Optional[str]:
        """Extract handler function name from route definition."""
        # Look for the last argument before the closing paren
        remaining = content[start_pos:start_pos + 200]
        
        # Match function name or arrow function
        match = re.search(r',\s*(\w+)\s*\)', remaining)
        if match:
            return match.group(1)
        
        return None
    
    def _extract_js_comment(self, lines: list[str], line_index: int) -> Optional[str]:
        """Extract JSDoc or comment above a line."""
        if line_index <= 0:
            return None
        
        # Look for JSDoc /** ... */
        for i in range(line_index - 1, max(0, line_index - 10), -1):
            line = lines[i].strip()
            if line.startswith("/**"):
                # Collect JSDoc content
                doc_lines = []
                for j in range(i, min(len(lines), i + 10)):
                    doc_line = lines[j].strip()
                    if doc_line.endswith("*/"):
                        break
                    # Extract description from JSDoc
                    clean = re.sub(r'^[\s*/]*', '', doc_line)
                    if clean and not clean.startswith("@"):
                        doc_lines.append(clean)
                return " ".join(doc_lines) if doc_lines else None
            elif not line.startswith("//") and not line.startswith("*") and line:
                break
        
        # Look for single-line comment
        prev_line = lines[line_index - 1].strip()
        if prev_line.startswith("//"):
            return prev_line[2:].strip()
        
        return None
    
    # ==================== Python ====================
    
    def _extract_python_routes(self, content: str, file_path: str) -> None:
        """Extract routes from Python code."""
        framework = self._detect_python_framework(content)
        
        if framework == Framework.FASTAPI:
            self._extract_fastapi_routes(content, file_path)
        elif framework == Framework.FLASK:
            self._extract_flask_routes(content, file_path)
        elif framework == Framework.DJANGO:
            self._extract_django_routes(content, file_path)
    
    def _detect_python_framework(self, content: str) -> Framework:
        """Detect Python framework from imports."""
        if re.search(r"from fastapi|import fastapi", content, re.IGNORECASE):
            return Framework.FASTAPI
        if re.search(r"from flask|import flask", content, re.IGNORECASE):
            return Framework.FLASK
        if re.search(r"from django|import django", content, re.IGNORECASE):
            return Framework.DJANGO
        return Framework.FLASK  # Default
    
    def _extract_fastapi_routes(self, content: str, file_path: str) -> None:
        """Extract routes from FastAPI code."""
        # Pattern for FastAPI decorators
        pattern = re.compile(
            r'@(?:app|router)\s*\.\s*(get|post|put|patch|delete|options|head)\s*\(\s*'
            r'[\'"]([^\'"]+)[\'"]',
            re.IGNORECASE | re.MULTILINE
        )
        
        lines = content.split("\n")
        
        for match in pattern.finditer(content):
            method = match.group(1).upper()
            path = match.group(2)
            line_num = content[:match.start()].count("\n") + 1
            
            # Find the function name (next def after decorator)
            handler = self._extract_python_handler(content, match.end())
            
            # Extract docstring
            description = self._extract_python_docstring(content, match.end())
            
            self.routes.append(ExtractedRoute(
                path=path,
                method=HTTPMethod(method),
                handler_name=handler,
                file_path=file_path,
                line_number=line_num,
                description=description,
                framework=Framework.FASTAPI,
            ))
    
    def _extract_flask_routes(self, content: str, file_path: str) -> None:
        """Extract routes from Flask code."""
        # Pattern for Flask route decorators
        pattern = re.compile(
            r'@(?:app|bp|blueprint)\s*\.route\s*\(\s*'
            r'[\'"]([^\'"]+)[\'"]'
            r'(?:\s*,\s*methods\s*=\s*\[([^\]]+)\])?',
            re.IGNORECASE | re.MULTILINE
        )
        
        for match in pattern.finditer(content):
            path = match.group(1)
            methods_str = match.group(2)
            line_num = content[:match.start()].count("\n") + 1
            
            # Parse methods or default to GET
            if methods_str:
                methods = [m.strip().strip("'\"").upper() for m in methods_str.split(",")]
            else:
                methods = ["GET"]
            
            handler = self._extract_python_handler(content, match.end())
            description = self._extract_python_docstring(content, match.end())
            
            for method in methods:
                self.routes.append(ExtractedRoute(
                    path=path,
                    method=HTTPMethod(method),
                    handler_name=handler,
                    file_path=file_path,
                    line_number=line_num,
                    description=description,
                    framework=Framework.FLASK,
                ))
    
    def _extract_django_routes(self, content: str, file_path: str) -> None:
        """Extract routes from Django URLs."""
        # Pattern for Django URL patterns
        patterns = [
            # path() function
            re.compile(
                r'path\s*\(\s*[\'"]([^\'"]+)[\'"]',
                re.MULTILINE
            ),
            # re_path() function
            re.compile(
                r're_path\s*\(\s*[\'"]([^\'"]+)[\'"]',
                re.MULTILINE
            ),
        ]
        
        for pattern in patterns:
            for match in pattern.finditer(content):
                path = match.group(1)
                line_num = content[:match.start()].count("\n") + 1
                
                self.routes.append(ExtractedRoute(
                    path=path,
                    method=HTTPMethod.ALL,  # Django routes handle all methods by default
                    file_path=file_path,
                    line_number=line_num,
                    framework=Framework.DJANGO,
                ))
    
    def _extract_python_handler(self, content: str, start_pos: int) -> Optional[str]:
        """Extract function name after a decorator."""
        remaining = content[start_pos:start_pos + 500]
        
        match = re.search(r'def\s+(\w+)\s*\(', remaining)
        if match:
            return match.group(1)
        
        return None
    
    def _extract_python_docstring(self, content: str, start_pos: int) -> Optional[str]:
        """Extract docstring from a Python function."""
        remaining = content[start_pos:start_pos + 1000]
        
        # Find def, then find docstring
        def_match = re.search(r'def\s+\w+\s*\([^)]*\)\s*(?:->[^:]+)?:\s*', remaining)
        if not def_match:
            return None
        
        after_def = remaining[def_match.end():].lstrip()
        
        # Check for docstring (single, double, or triple quotes)
        for quote in ['"""', "'''", '"', "'"]:
            if after_def.startswith(quote):
                end_quote = after_def.find(quote, len(quote))
                if end_quote > 0:
                    docstring = after_def[len(quote):end_quote].strip()
                    # Get first line/sentence
                    return docstring.split("\n")[0].strip()
        
        return None
    
    # ==================== Go ====================
    
    def _extract_go_routes(self, content: str, file_path: str) -> None:
        """Extract routes from Go code."""
        framework = self._detect_go_framework(content)
        
        if framework == Framework.GIN:
            self._extract_gin_routes(content, file_path)
        elif framework == Framework.GORILLA:
            self._extract_gorilla_routes(content, file_path)
        elif framework == Framework.CHI:
            self._extract_chi_routes(content, file_path)
        elif framework == Framework.FIBER:
            self._extract_fiber_routes(content, file_path)
        else:
            # Try standard net/http
            self._extract_nethttp_routes(content, file_path)
    
    def _detect_go_framework(self, content: str) -> Framework:
        """Detect Go framework from imports."""
        if re.search(r'"github\.com/gin-gonic/gin"', content):
            return Framework.GIN
        if re.search(r'"github\.com/gorilla/mux"', content):
            return Framework.GORILLA
        if re.search(r'"github\.com/go-chi/chi"', content):
            return Framework.CHI
        if re.search(r'"github\.com/gofiber/fiber"', content):
            return Framework.FIBER
        return Framework.UNKNOWN
    
    def _extract_gin_routes(self, content: str, file_path: str) -> None:
        """Extract routes from Gin framework code."""
        pattern = re.compile(
            r'(?:r|router|group|g)\s*\.\s*(GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD)\s*\(\s*'
            r'"([^"]+)"',
            re.MULTILINE
        )
        
        for match in pattern.finditer(content):
            method = match.group(1)
            path = match.group(2)
            line_num = content[:match.start()].count("\n") + 1
            
            self.routes.append(ExtractedRoute(
                path=path,
                method=HTTPMethod(method),
                file_path=file_path,
                line_number=line_num,
                framework=Framework.GIN,
            ))
    
    def _extract_gorilla_routes(self, content: str, file_path: str) -> None:
        """Extract routes from Gorilla Mux code."""
        pattern = re.compile(
            r'(?:r|router|mux)\s*\.\s*HandleFunc\s*\(\s*'
            r'"([^"]+)"'
            r'[^)]*\)\s*\.Methods\s*\(\s*'
            r'"([^"]+)"',
            re.MULTILINE
        )
        
        for match in pattern.finditer(content):
            path = match.group(1)
            method = match.group(2)
            line_num = content[:match.start()].count("\n") + 1
            
            self.routes.append(ExtractedRoute(
                path=path,
                method=HTTPMethod(method),
                file_path=file_path,
                line_number=line_num,
                framework=Framework.GORILLA,
            ))
    
    def _extract_chi_routes(self, content: str, file_path: str) -> None:
        """Extract routes from Chi framework code."""
        pattern = re.compile(
            r'(?:r|router)\s*\.\s*(Get|Post|Put|Patch|Delete|Options|Head)\s*\(\s*'
            r'"([^"]+)"',
            re.MULTILINE
        )
        
        for match in pattern.finditer(content):
            method = match.group(1).upper()
            path = match.group(2)
            line_num = content[:match.start()].count("\n") + 1
            
            self.routes.append(ExtractedRoute(
                path=path,
                method=HTTPMethod(method),
                file_path=file_path,
                line_number=line_num,
                framework=Framework.CHI,
            ))
    
    def _extract_fiber_routes(self, content: str, file_path: str) -> None:
        """Extract routes from Fiber framework code."""
        pattern = re.compile(
            r'(?:app|router)\s*\.\s*(Get|Post|Put|Patch|Delete|Options|Head)\s*\(\s*'
            r'"([^"]+)"',
            re.MULTILINE
        )
        
        for match in pattern.finditer(content):
            method = match.group(1).upper()
            path = match.group(2)
            line_num = content[:match.start()].count("\n") + 1
            
            self.routes.append(ExtractedRoute(
                path=path,
                method=HTTPMethod(method),
                file_path=file_path,
                line_number=line_num,
                framework=Framework.FIBER,
            ))
    
    def _extract_nethttp_routes(self, content: str, file_path: str) -> None:
        """Extract routes from standard net/http code."""
        pattern = re.compile(
            r'http\.HandleFunc\s*\(\s*"([^"]+)"',
            re.MULTILINE
        )
        
        for match in pattern.finditer(content):
            path = match.group(1)
            line_num = content[:match.start()].count("\n") + 1
            
            self.routes.append(ExtractedRoute(
                path=path,
                method=HTTPMethod.ALL,  # net/http handles all methods
                file_path=file_path,
                line_number=line_num,
                framework=Framework.UNKNOWN,
            ))
