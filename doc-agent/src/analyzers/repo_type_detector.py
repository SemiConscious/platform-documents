"""
Repository type detection.

Detects the type of repository based on files, structure, and content
to enable type-specific documentation strategies.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger("doc-agent.analyzers.repo_type_detector")


class RepoType(Enum):
    """Types of repositories for documentation purposes."""
    API_SERVICE = "api_service"           # REST/GraphQL APIs (PHP, Go, TypeScript)
    TERRAFORM = "terraform"               # Infrastructure as Code
    LAMBDA = "lambda"                     # Serverless functions
    LIBRARY = "library"                   # Shared libraries/SDKs
    TELEPHONY = "telephony"               # FreeSWITCH/OpenSIPs/VoIP
    SALESFORCE = "salesforce"             # Salesforce packages
    FRONTEND = "frontend"                 # Web applications
    MOBILE = "mobile"                     # Mobile applications
    DATA_PIPELINE = "data_pipeline"       # ETL/data processing
    DOCKER = "docker"                     # Container definitions
    ANSIBLE = "ansible"                   # Configuration management
    KUBERNETES = "kubernetes"             # K8s manifests
    DOCUMENTATION = "documentation"       # Pure documentation repos
    MONOREPO = "monorepo"                 # Multi-project repositories
    UNKNOWN = "unknown"


@dataclass
class RepoTypeResult:
    """Result of repository type detection."""
    primary_type: RepoType
    secondary_types: list[RepoType] = field(default_factory=list)
    confidence: float = 1.0
    indicators_found: list[str] = field(default_factory=list)
    languages_detected: list[str] = field(default_factory=list)
    frameworks_detected: list[str] = field(default_factory=list)
    
    @property
    def is_hybrid(self) -> bool:
        """Check if this is a hybrid/multi-type repository."""
        return len(self.secondary_types) > 0


# File patterns that indicate repository types
TYPE_INDICATORS: dict[RepoType, dict] = {
    RepoType.TERRAFORM: {
        "files": ["main.tf", "variables.tf", "outputs.tf", "terraform.tfvars", "providers.tf"],
        "patterns": ["*.tf", "*.tfvars"],
        "directories": [".terraform", "modules/"],
    },
    RepoType.LAMBDA: {
        "files": ["serverless.yml", "serverless.yaml", "template.yaml", "template.yml", 
                  "sam.yaml", "lambda_function.py", "handler.py", "index.handler.js"],
        "patterns": ["lambda*.py", "handler*.py", "handler*.js", "handler*.ts"],
        "directories": [".serverless/"],
        "content_patterns": ["AWS::Lambda", "aws_lambda_function", "lambda.handler"],
    },
    RepoType.SALESFORCE: {
        "files": ["sfdx-project.json", "package.xml"],
        "patterns": ["*.cls", "*.trigger", "*.object", "*.page"],
        "directories": ["force-app/", "src/classes/", "src/triggers/"],
    },
    RepoType.TELEPHONY: {
        "files": ["dialplan.xml", "freeswitch.xml", "opensips.cfg", "kamailio.cfg", 
                  "sofia.conf.xml", "vars.xml"],
        "patterns": ["*.lua"],  # FreeSWITCH uses Lua - removed *.xml as too generic
        "directories": ["dialplan/", "conf/freeswitch/", "scripts/freeswitch/"],
        "content_patterns": ["freeswitch", "opensips", "kamailio", "sofia", "originate", "bridge"],
    },
    RepoType.FRONTEND: {
        "files": ["package.json", "next.config.js", "nuxt.config.js", "vite.config.js",
                  "angular.json", "vue.config.js", ".babelrc"],
        "patterns": ["*.jsx", "*.tsx", "*.vue", "*.svelte"],
        "directories": ["src/components/", "src/pages/", "public/", "static/"],
        "content_patterns": ["react", "vue", "angular", "svelte", "next", "nuxt"],
    },
    RepoType.MOBILE: {
        "files": ["App.tsx", "app.json", "metro.config.js", "Podfile", 
                  "build.gradle", "AndroidManifest.xml", "Info.plist"],
        "directories": ["ios/", "android/", "lib/"],  # Flutter uses lib/
        "content_patterns": ["react-native", "flutter", "expo"],
    },
    RepoType.DATA_PIPELINE: {
        "files": ["dags/", "pipeline.py", "etl.py", "airflow.cfg", "dagster.yaml"],
        "patterns": ["*_dag.py", "*_pipeline.py", "*_etl.py"],
        "directories": ["dags/", "pipelines/", "notebooks/"],
        "content_patterns": ["airflow", "dagster", "prefect", "luigi", "spark"],
    },
    RepoType.DOCKER: {
        "files": ["Dockerfile", "docker-compose.yml", "docker-compose.yaml", 
                  ".dockerignore", "compose.yml", "compose.yaml"],
        "directories": [],
    },
    RepoType.ANSIBLE: {
        "files": ["ansible.cfg", "playbook.yml", "site.yml", "inventory.ini"],
        "patterns": ["*.yml", "*.yaml"],
        "directories": ["roles/", "playbooks/", "inventories/", "group_vars/", "host_vars/"],
    },
    RepoType.KUBERNETES: {
        "files": ["kustomization.yaml", "Chart.yaml", "values.yaml"],
        "patterns": ["*.yaml", "*.yml"],
        "directories": ["charts/", "manifests/", "k8s/", "kubernetes/", "helm/"],
        "content_patterns": ["apiVersion:", "kind: Deployment", "kind: Service", "kind: Pod"],
    },
    RepoType.LIBRARY: {
        "files": ["setup.py", "pyproject.toml", "Cargo.toml", "go.mod", 
                  "package.json", "*.gemspec", "pom.xml", "build.gradle"],
        # Libraries usually have these WITHOUT controller/handler patterns
        "directories": ["src/", "lib/", "pkg/"],
    },
    RepoType.API_SERVICE: {
        "files": ["swagger.json", "openapi.yaml", "openapi.json", "api.yaml",
                  "routes.py", "routes.ts", "controllers/", "composer.json"],
        "patterns": ["*_controller.php", "*_controller.go", "*Controller.ts", "*Controller.java",
                     "*Controller.php"],  # Added uppercase pattern
        "directories": ["controllers/", "handlers/", "routes/", "api/", "endpoints/",
                        "application/controllers/",  # Kohana pattern
                        "application/classes/controller/"],  # Kohana 3.x pattern
        "content_patterns": ["@RestController", "@Controller", "Route::", "app.get(", "router.",
                             "RestfulBase_Controller", "_validationRules",  # Kohana REST patterns
                             "@route", "@api", "APIController"],
    },
    RepoType.DOCUMENTATION: {
        "files": ["mkdocs.yml", "docusaurus.config.js", "_config.yml", "book.toml"],
        "patterns": ["*.md", "*.rst", "*.adoc"],
        "directories": ["docs/", "documentation/", "content/", "_posts/"],
    },
}

# Framework detection patterns
FRAMEWORK_PATTERNS: dict[str, list[str]] = {
    # PHP Frameworks
    "kohana": ["Kohana", "kohana", "_Controller", "_Model"],
    "laravel": ["Laravel", "Illuminate", "artisan"],
    "symfony": ["Symfony", "symfony", "AppBundle"],
    
    # Python Frameworks
    "flask": ["Flask", "flask", "@app.route"],
    "fastapi": ["FastAPI", "fastapi", "@app.get", "@app.post"],
    "django": ["Django", "django", "urls.py", "views.py"],
    
    # Go Frameworks
    "gin": ["gin.Context", "gin.Engine", "gin.Default()"],
    "echo": ["echo.Context", "echo.New()"],
    "chi": ["chi.Router", "chi.NewRouter()"],
    
    # Node/TS Frameworks
    "express": ["express", "Express", "app.listen", "router.get"],
    "nestjs": ["@nestjs", "@Controller", "@Injectable", "@Module"],
    "hono": ["Hono", "hono", "c.json"],
    "nextjs": ["next/", "getServerSideProps", "getStaticProps"],
    
    # Telephony
    "freeswitch": ["freeswitch", "FreeSWITCH", "mod_", "sofia", "dialplan"],
    "opensips": ["opensips", "OpenSIPS", "route{", "modparam"],
    "kamailio": ["kamailio", "Kamailio"],
}


def detect_repo_type(repo_path: Path) -> RepoTypeResult:
    """
    Detect the type of repository from its structure and content.
    
    Args:
        repo_path: Path to the repository root
        
    Returns:
        RepoTypeResult with detected type(s) and confidence
    """
    if not repo_path.exists():
        return RepoTypeResult(primary_type=RepoType.UNKNOWN, confidence=0.0)
    
    scores: dict[RepoType, float] = {t: 0.0 for t in RepoType}
    indicators_found: list[str] = []
    languages_detected: list[str] = []
    frameworks_detected: list[str] = []
    
    # Check each type's indicators
    for repo_type, indicators in TYPE_INDICATORS.items():
        type_score = 0.0
        
        # Check for specific files
        for filename in indicators.get("files", []):
            if (repo_path / filename).exists():
                type_score += 2.0
                indicators_found.append(f"{repo_type.value}:{filename}")
        
        # Check for file patterns
        for pattern in indicators.get("patterns", []):
            matches = list(repo_path.rglob(pattern))[:10]  # Limit search
            if matches:
                type_score += min(len(matches) * 0.5, 3.0)
                indicators_found.append(f"{repo_type.value}:{pattern}({len(matches)})")
        
        # Check for directories
        for dirname in indicators.get("directories", []):
            if (repo_path / dirname).exists():
                type_score += 1.5
                indicators_found.append(f"{repo_type.value}:{dirname}/")
        
        # Check content patterns in key files
        content_patterns = indicators.get("content_patterns", [])
        if content_patterns:
            type_score += _check_content_patterns(repo_path, content_patterns)
        
        scores[repo_type] = type_score
    
    # Detect languages
    languages_detected = _detect_languages(repo_path)
    
    # Detect frameworks
    frameworks_detected = _detect_frameworks(repo_path)
    
    # Adjust scores based on framework detection
    for framework in frameworks_detected:
        if framework in ["flask", "fastapi", "django", "express", "nestjs", "gin", "echo", "chi", "hono", "kohana", "laravel", "symfony"]:
            scores[RepoType.API_SERVICE] += 3.0
        elif framework in ["freeswitch", "opensips", "kamailio"]:
            scores[RepoType.TELEPHONY] += 5.0
        elif framework in ["nextjs"]:
            scores[RepoType.FRONTEND] += 3.0
    
    # Sort by score
    sorted_types = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    
    # Determine primary and secondary types
    primary_type = RepoType.UNKNOWN
    secondary_types = []
    
    if sorted_types[0][1] > 0:
        primary_type = sorted_types[0][0]
        
        # Find secondary types with significant scores
        primary_score = sorted_types[0][1]
        for repo_type, score in sorted_types[1:]:
            if score >= primary_score * 0.5 and score > 2.0:
                secondary_types.append(repo_type)
    
    # Calculate confidence
    total_score = sum(s for _, s in sorted_types)
    confidence = sorted_types[0][1] / total_score if total_score > 0 else 0.0
    
    # Special case: monorepo detection
    if len(secondary_types) >= 2 or _looks_like_monorepo(repo_path):
        secondary_types.insert(0, primary_type)
        primary_type = RepoType.MONOREPO
        confidence = 0.8
    
    return RepoTypeResult(
        primary_type=primary_type,
        secondary_types=secondary_types,
        confidence=min(confidence, 1.0),
        indicators_found=indicators_found,
        languages_detected=languages_detected,
        frameworks_detected=frameworks_detected,
    )


def _check_content_patterns(repo_path: Path, patterns: list[str]) -> float:
    """Check for content patterns in key files."""
    score = 0.0
    
    # Files to check for content patterns
    files_to_check = [
        "README.md", "README.rst", "README.txt",
        "package.json", "composer.json", "go.mod", "Cargo.toml",
        "main.py", "main.go", "index.ts", "index.js", "app.php",
    ]
    
    for filename in files_to_check:
        filepath = repo_path / filename
        if filepath.exists():
            try:
                content = filepath.read_text(errors='ignore')[:10000]
                for pattern in patterns:
                    if pattern.lower() in content.lower():
                        score += 1.0
            except Exception:
                pass
    
    return min(score, 5.0)


def _detect_languages(repo_path: Path) -> list[str]:
    """Detect programming languages in the repository."""
    languages = set()
    
    language_extensions = {
        ".py": "python",
        ".go": "go",
        ".php": "php",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".js": "javascript",
        ".jsx": "javascript",
        ".java": "java",
        ".rs": "rust",
        ".rb": "ruby",
        ".cs": "csharp",
        ".cpp": "cpp",
        ".c": "c",
        ".lua": "lua",
        ".sh": "bash",
        ".tf": "terraform",
        ".cls": "apex",
        ".trigger": "apex",
    }
    
    # Sample files to detect languages
    for ext, lang in language_extensions.items():
        matches = list(repo_path.rglob(f"*{ext}"))[:5]
        if matches:
            languages.add(lang)
    
    return sorted(languages)


def _detect_frameworks(repo_path: Path) -> list[str]:
    """Detect frameworks used in the repository."""
    detected = set()
    
    # Check package files for framework dependencies
    package_files = [
        ("package.json", ["dependencies", "devDependencies"]),
        ("composer.json", ["require", "require-dev"]),
        ("requirements.txt", None),
        ("go.mod", None),
        ("Cargo.toml", ["dependencies"]),
    ]
    
    for filename, keys in package_files:
        filepath = repo_path / filename
        if filepath.exists():
            try:
                content = filepath.read_text(errors='ignore')
                for framework, patterns in FRAMEWORK_PATTERNS.items():
                    for pattern in patterns:
                        if pattern in content:
                            detected.add(framework)
                            break
            except Exception:
                pass
    
    # Check source files for framework patterns
    source_files = list(repo_path.rglob("*.py"))[:20] + \
                   list(repo_path.rglob("*.go"))[:20] + \
                   list(repo_path.rglob("*.php"))[:20] + \
                   list(repo_path.rglob("*.ts"))[:20] + \
                   list(repo_path.rglob("*.js"))[:20]
    
    for filepath in source_files:
        try:
            content = filepath.read_text(errors='ignore')[:5000]
            for framework, patterns in FRAMEWORK_PATTERNS.items():
                if framework not in detected:
                    for pattern in patterns:
                        if pattern in content:
                            detected.add(framework)
                            break
        except Exception:
            pass
    
    return sorted(detected)


def _looks_like_monorepo(repo_path: Path) -> bool:
    """Check if repository looks like a monorepo."""
    # Common monorepo indicators
    monorepo_files = ["lerna.json", "pnpm-workspace.yaml", "rush.json", "nx.json"]
    for f in monorepo_files:
        if (repo_path / f).exists():
            return True
    
    # Check for packages/ or apps/ directories with multiple projects
    for dirname in ["packages", "apps", "services", "modules"]:
        dirpath = repo_path / dirname
        if dirpath.exists() and dirpath.is_dir():
            subdirs = [d for d in dirpath.iterdir() if d.is_dir()]
            if len(subdirs) >= 3:
                return True
    
    return False


def get_documentation_requirements(repo_type: RepoType) -> dict:
    """
    Get documentation requirements for a repository type.
    
    Returns a dict with required documents, quality criteria, and templates.
    """
    requirements = {
        RepoType.API_SERVICE: {
            "required_docs": [
                "README.md",
                "api/README.md",
                "architecture.md",
                "data/models.md",
                "data/side-effects.md",
                "operations.md",
                "configuration.md",
            ],
            "quality_criteria": {
                "endpoints_documented": 0.90,
                "request_response_examples": 0.85,
                "database_side_effects": 0.80,
                "architecture_diagram": True,
                "error_codes": 0.75,
            },
        },
        RepoType.TERRAFORM: {
            "required_docs": [
                "README.md",
                "architecture.md",
                "resources.md",
                "variables.md",
                "outputs.md",
                "data-flows.md",
                "consumers.md",
            ],
            "quality_criteria": {
                "infrastructure_diagram": True,
                "all_variables_documented": 0.95,
                "all_outputs_documented": 0.95,
                "consumer_list": 0.80,
                "data_flow_diagram": 0.75,
            },
        },
        RepoType.LAMBDA: {
            "required_docs": [
                "README.md",
                "api.md",
                "triggers.md",
                "dependencies.md",
                "data-flows.md",
                "operations.md",
            ],
            "quality_criteria": {
                "event_schema_documented": 0.90,
                "trigger_documented": True,
                "iam_permissions": 0.85,
                "error_handling": 0.80,
            },
        },
        RepoType.LIBRARY: {
            "required_docs": [
                "README.md",
                "installation.md",
                "api-reference.md",
                "examples.md",
                "architecture.md",
            ],
            "quality_criteria": {
                "public_api_documented": 0.95,
                "installation_instructions": True,
                "working_examples": 0.85,
            },
        },
        RepoType.TELEPHONY: {
            "required_docs": [
                "README.md",
                "dial-plan.md",
                "integrations.md",
                "call-flows.md",
                "events.md",
                "operations.md",
            ],
            "quality_criteria": {
                "call_flow_diagrams": 0.85,
                "dial_plan_documented": 0.90,
                "event_catalog": 0.80,
                "integration_points": 0.85,
            },
        },
        RepoType.SALESFORCE: {
            "required_docs": [
                "README.md",
                "objects.md",
                "apex-classes.md",
                "triggers.md",
                "flows.md",
                "lwc-components.md",
                "integrations.md",
            ],
            "quality_criteria": {
                "custom_objects_documented": 0.95,
                "apex_documented": 0.90,
                "soql_operations": 0.85,
                "callouts_documented": 0.90,
            },
        },
        RepoType.FRONTEND: {
            "required_docs": [
                "README.md",
                "architecture.md",
                "components.md",
                "state-management.md",
                "api-integration.md",
            ],
            "quality_criteria": {
                "component_catalog": 0.85,
                "architecture_diagram": True,
                "state_flow": 0.75,
            },
        },
        RepoType.KUBERNETES: {
            "required_docs": [
                "README.md",
                "architecture.md",
                "resources.md",
                "deployment.md",
                "networking.md",
            ],
            "quality_criteria": {
                "resource_diagram": True,
                "deployment_documented": 0.90,
                "networking_documented": 0.85,
            },
        },
    }
    
    return requirements.get(repo_type, {
        "required_docs": ["README.md"],
        "quality_criteria": {},
    })
