"""
Discovery agents for gathering data from sources.

Primary agents (used in pipeline):
- RepositoryScannerAgent: Discover services from GitHub repos
- CodeAnalyzerAgent: Deep analysis of code for APIs/schemas

Legacy/Deprecated (replaced by enrichment agents):
- ConfluenceHarvesterAgent: Replaced by ConfluenceEnricherAgent
- Docs360HarvesterAgent: Replaced by Docs360EnricherAgent
- JiraAnalyzerAgent: Disabled by default (not useful for architecture docs)
"""

from .repo_scanner import RepositoryScannerAgent
from .confluence_harvester import ConfluenceHarvesterAgent
from .jira_analyzer import JiraAnalyzerAgent
from .code_analyzer import CodeAnalyzerAgent
from .docs360_harvester import Docs360HarvesterAgent

__all__ = [
    "RepositoryScannerAgent",
    "CodeAnalyzerAgent",
    # Legacy (kept for backwards compatibility)
    "ConfluenceHarvesterAgent",
    "JiraAnalyzerAgent",
    "Docs360HarvesterAgent",
]
