"""Jira operations via the Natterbox MCP server."""

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

from .client import MCPClient

logger = logging.getLogger("doc-agent.mcp.jira")


@dataclass
class JiraIssue:
    """Jira issue information."""
    key: str
    summary: str
    description: str = ""
    issue_type: str = ""
    status: str = ""
    priority: str = ""
    assignee: str = ""
    reporter: str = ""
    labels: list[str] = field(default_factory=list)
    components: list[str] = field(default_factory=list)
    url: str = ""
    created: str = ""
    updated: str = ""
    
    @classmethod
    def from_dict(cls, data: dict) -> "JiraIssue":
        fields = data.get("fields", data)
        
        # Extract nested values safely
        assignee = fields.get("assignee", {})
        if isinstance(assignee, dict):
            assignee = assignee.get("displayName", assignee.get("emailAddress", ""))
        
        reporter = fields.get("reporter", {})
        if isinstance(reporter, dict):
            reporter = reporter.get("displayName", reporter.get("emailAddress", ""))
        
        issue_type = fields.get("issuetype", {})
        if isinstance(issue_type, dict):
            issue_type = issue_type.get("name", "")
        
        status = fields.get("status", {})
        if isinstance(status, dict):
            status = status.get("name", "")
        
        priority = fields.get("priority", {})
        if isinstance(priority, dict):
            priority = priority.get("name", "")
        
        components = []
        for comp in fields.get("components", []):
            if isinstance(comp, dict):
                components.append(comp.get("name", ""))
            elif isinstance(comp, str):
                components.append(comp)
        
        return cls(
            key=data.get("key", ""),
            summary=fields.get("summary", ""),
            description=fields.get("description") or "",
            issue_type=issue_type if isinstance(issue_type, str) else "",
            status=status if isinstance(status, str) else "",
            priority=priority if isinstance(priority, str) else "",
            assignee=assignee if isinstance(assignee, str) else "",
            reporter=reporter if isinstance(reporter, str) else "",
            labels=fields.get("labels", []),
            components=components,
            url=data.get("self", ""),
            created=fields.get("created", ""),
            updated=fields.get("updated", ""),
        )


@dataclass
class JiraProject:
    """Jira project information."""
    key: str
    name: str
    description: str = ""
    url: str = ""
    lead: str = ""
    
    @classmethod
    def from_dict(cls, data: dict) -> "JiraProject":
        lead = data.get("lead", {})
        if isinstance(lead, dict):
            lead = lead.get("displayName", "")
        
        return cls(
            key=data.get("key", ""),
            name=data.get("name", ""),
            description=data.get("description") or "",
            url=data.get("self", ""),
            lead=lead if isinstance(lead, str) else "",
        )


@dataclass
class JiraComponent:
    """Jira component information."""
    id: str
    name: str
    description: str = ""
    lead: str = ""
    
    @classmethod
    def from_dict(cls, data: dict) -> "JiraComponent":
        lead = data.get("lead", {})
        if isinstance(lead, dict):
            lead = lead.get("displayName", "")
        
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            description=data.get("description") or "",
            lead=lead if isinstance(lead, str) else "",
        )


class JiraClient:
    """
    Jira operations via the Natterbox MCP server.
    
    Uses the 'jira' MCP tool with operation parameter.
    """
    
    TOOL_NAME = "jira"
    
    def __init__(self, mcp_client: MCPClient):
        self.mcp = mcp_client
    
    async def search_issues(
        self,
        query: str,
        project_key: Optional[str] = None,
    ) -> list[JiraIssue]:
        """
        Search for Jira issues.
        
        Args:
            query: JQL or natural language query
            project_key: Optional project to filter
            
        Returns:
            List of matching issues
        """
        search_query = query
        if project_key:
            search_query = f'project = "{project_key}" AND ({query})'
        
        response = await self.mcp.call_tool(self.TOOL_NAME, {
            "operation": "search_issues",
            "query": search_query,
        })
        
        if not response.success:
            logger.error(f"Search failed: {response.error}")
            return []
        
        issues = []
        data = response.data
        
        # Handle various response formats
        results = []
        if isinstance(data, list):
            results = data
        elif isinstance(data, dict):
            results = data.get("issues", data.get("results", []))
        
        for issue_data in results:
            try:
                issues.append(JiraIssue.from_dict(issue_data))
            except Exception as e:
                logger.warning(f"Failed to parse issue: {e}")
        
        return issues
    
    async def get_issue(
        self,
        issue_key: str,
    ) -> Optional[JiraIssue]:
        """Get a specific issue by key."""
        response = await self.mcp.call_tool(self.TOOL_NAME, {
            "operation": "get_issue",
            "issueKey": issue_key,
        })
        
        if not response.success:
            logger.error(f"Get issue failed: {response.error}")
            return None
        
        if response.data:
            return JiraIssue.from_dict(response.data)
        return None
    
    async def list_projects(self) -> list[JiraProject]:
        """List all accessible Jira projects."""
        response = await self.mcp.call_tool(self.TOOL_NAME, {
            "operation": "list_projects",
        })
        
        if not response.success:
            logger.error(f"List projects failed: {response.error}")
            return []
        
        projects = []
        data = response.data
        
        results = []
        if isinstance(data, list):
            results = data
        elif isinstance(data, dict):
            results = data.get("projects", data.get("values", []))
        
        for project_data in results:
            try:
                projects.append(JiraProject.from_dict(project_data))
            except Exception as e:
                logger.warning(f"Failed to parse project: {e}")
        
        return projects
    
    async def get_project(
        self,
        project_key: str,
    ) -> Optional[JiraProject]:
        """Get project information."""
        response = await self.mcp.call_tool(self.TOOL_NAME, {
            "operation": "get_project",
            "projectKey": project_key,
        })
        
        if not response.success:
            logger.error(f"Get project failed: {response.error}")
            return None
        
        if response.data:
            return JiraProject.from_dict(response.data)
        return None
    
    async def get_epics(
        self,
        project_key: str,
    ) -> list[JiraIssue]:
        """Get all epics in a project."""
        return await self.search_issues(
            f'project = "{project_key}" AND issuetype = Epic ORDER BY created DESC'
        )
    
    async def get_stories_for_epic(
        self,
        epic_key: str,
    ) -> list[JiraIssue]:
        """Get all stories linked to an epic."""
        return await self.search_issues(
            f'"Epic Link" = {epic_key} OR parent = {epic_key}'
        )
    
    async def get_technical_debt(
        self,
        project_key: str,
    ) -> list[JiraIssue]:
        """Find technical debt issues in a project."""
        return await self.search_issues(
            f'project = "{project_key}" AND (issuetype = "Technical Debt" OR labels = tech-debt OR labels = technical-debt)'
        )
    
    async def get_bugs(
        self,
        project_key: str,
        status: str = "Open",
    ) -> list[JiraIssue]:
        """Get bugs in a project."""
        return await self.search_issues(
            f'project = "{project_key}" AND issuetype = Bug AND status = "{status}"'
        )
    
    async def get_recent_releases(
        self,
        project_key: str,
    ) -> list[JiraIssue]:
        """Get recent releases (issues with fixVersion)."""
        return await self.search_issues(
            f'project = "{project_key}" AND fixVersion is not EMPTY ORDER BY updated DESC'
        )
    
    async def extract_feature_documentation(
        self,
        project_keys: list[str],
    ) -> list[JiraIssue]:
        """
        Extract feature documentation from epics and stories.
        
        Returns epics with detailed descriptions that can be used
        for documentation.
        """
        all_features = []
        
        for project_key in project_keys:
            try:
                # Get epics
                epics = await self.get_epics(project_key)
                all_features.extend(epics)
                
                # Get high-level stories with descriptions
                stories = await self.search_issues(
                    f'project = "{project_key}" AND issuetype = Story AND description is not EMPTY ORDER BY created DESC'
                )
                all_features.extend(stories[:50])  # Limit stories
                
            except Exception as e:
                logger.warning(f"Failed to get features from {project_key}: {e}")
        
        return all_features
    
    async def analyze_bug_patterns(
        self,
        project_key: str,
    ) -> dict[str, Any]:
        """
        Analyze bug patterns in a project.
        
        Returns statistics about bugs by component, priority, etc.
        """
        bugs = await self.search_issues(
            f'project = "{project_key}" AND issuetype = Bug'
        )
        
        # Analyze patterns
        by_component: dict[str, int] = {}
        by_priority: dict[str, int] = {}
        by_status: dict[str, int] = {}
        
        for bug in bugs:
            # By component
            for comp in bug.components:
                by_component[comp] = by_component.get(comp, 0) + 1
            
            # By priority
            if bug.priority:
                by_priority[bug.priority] = by_priority.get(bug.priority, 0) + 1
            
            # By status
            if bug.status:
                by_status[bug.status] = by_status.get(bug.status, 0) + 1
        
        return {
            "total_bugs": len(bugs),
            "by_component": by_component,
            "by_priority": by_priority,
            "by_status": by_status,
        }
