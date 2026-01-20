"""Jira-specific MCP operations."""

import logging
from typing import Any, Optional
from dataclasses import dataclass
from datetime import datetime

from .client import MCPClient

logger = logging.getLogger("doc-agent.mcp.jira")


@dataclass
class JiraIssue:
    """Jira issue information."""
    key: str
    summary: str
    description: Optional[str]
    issue_type: str
    status: str
    priority: Optional[str]
    project: str
    url: str
    created: Optional[datetime]
    updated: Optional[datetime]
    resolved: Optional[datetime]
    assignee: Optional[str]
    reporter: Optional[str]
    labels: list[str]
    components: list[str]
    epic_key: Optional[str]
    parent_key: Optional[str]
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "JiraIssue":
        fields = data.get("fields", data)
        
        created = None
        updated = None
        resolved = None
        
        if fields.get("created"):
            try:
                created = datetime.fromisoformat(fields["created"].replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                pass
        
        if fields.get("updated"):
            try:
                updated = datetime.fromisoformat(fields["updated"].replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                pass
        
        if fields.get("resolutiondate"):
            try:
                resolved = datetime.fromisoformat(fields["resolutiondate"].replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                pass
        
        return cls(
            key=data.get("key", ""),
            summary=fields.get("summary", ""),
            description=fields.get("description"),
            issue_type=fields.get("issuetype", {}).get("name", "") if isinstance(fields.get("issuetype"), dict) else fields.get("issue_type", ""),
            status=fields.get("status", {}).get("name", "") if isinstance(fields.get("status"), dict) else fields.get("status", ""),
            priority=fields.get("priority", {}).get("name") if isinstance(fields.get("priority"), dict) else fields.get("priority"),
            project=fields.get("project", {}).get("key", "") if isinstance(fields.get("project"), dict) else fields.get("project", ""),
            url=data.get("url", data.get("self", "")),
            created=created,
            updated=updated,
            resolved=resolved,
            assignee=fields.get("assignee", {}).get("displayName") if isinstance(fields.get("assignee"), dict) else fields.get("assignee"),
            reporter=fields.get("reporter", {}).get("displayName") if isinstance(fields.get("reporter"), dict) else fields.get("reporter"),
            labels=fields.get("labels", []),
            components=[c.get("name", c) if isinstance(c, dict) else c for c in fields.get("components", [])],
            epic_key=fields.get("epic", {}).get("key") if isinstance(fields.get("epic"), dict) else fields.get("epic_key"),
            parent_key=fields.get("parent", {}).get("key") if isinstance(fields.get("parent"), dict) else fields.get("parent_key"),
        )


@dataclass
class JiraProject:
    """Jira project information."""
    key: str
    name: str
    description: Optional[str]
    url: str
    lead: Optional[str]
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "JiraProject":
        return cls(
            key=data.get("key", ""),
            name=data.get("name", ""),
            description=data.get("description"),
            url=data.get("url", data.get("self", "")),
            lead=data.get("lead", {}).get("displayName") if isinstance(data.get("lead"), dict) else data.get("lead"),
        )


@dataclass 
class JiraComponent:
    """Jira component information."""
    id: str
    name: str
    description: Optional[str]
    lead: Optional[str]
    project: str
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "JiraComponent":
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            description=data.get("description"),
            lead=data.get("lead", {}).get("displayName") if isinstance(data.get("lead"), dict) else data.get("lead"),
            project=data.get("project", ""),
        )


class JiraClient:
    """
    Jira-specific operations through MCP.
    
    Provides methods for searching issues, extracting technical context,
    and understanding project structure.
    """
    
    def __init__(self, mcp_client: MCPClient):
        """
        Initialize the Jira client.
        
        Args:
            mcp_client: The MCP client to use for requests
        """
        self.mcp = mcp_client
    
    async def get_project(self, project_key: str) -> Optional[JiraProject]:
        """
        Get information about a Jira project.
        
        Args:
            project_key: The project key (e.g., "PLAT")
            
        Returns:
            JiraProject object or None
        """
        response = await self.mcp.call_tool(
            "jira_get_project",
            {"project_key": project_key}
        )
        
        if not response.success:
            logger.error(f"Failed to get project {project_key}: {response.error}")
            return None
        
        return JiraProject.from_dict(response.data)
    
    async def get_components(self, project_key: str) -> list[JiraComponent]:
        """
        Get components for a Jira project.
        
        Args:
            project_key: The project key
            
        Returns:
            List of JiraComponent objects
        """
        response = await self.mcp.call_tool(
            "jira_get_components",
            {"project_key": project_key}
        )
        
        if not response.success:
            logger.error(f"Failed to get components for {project_key}: {response.error}")
            return []
        
        return [JiraComponent.from_dict(c) for c in response.data or []]
    
    async def search_issues(
        self,
        jql: str,
        max_results: int = 100,
    ) -> list[JiraIssue]:
        """
        Search for issues using JQL.
        
        Args:
            jql: JQL query string
            max_results: Maximum number of results
            
        Returns:
            List of JiraIssue objects
        """
        response = await self.mcp.call_tool(
            "jira_search",
            {"jql": jql, "max_results": max_results}
        )
        
        if not response.success:
            logger.error(f"Search failed: {response.error}")
            return []
        
        issues = response.data.get("issues", response.data) if isinstance(response.data, dict) else response.data
        return [JiraIssue.from_dict(i) for i in issues or []]
    
    async def get_issue(self, issue_key: str) -> Optional[JiraIssue]:
        """
        Get a specific Jira issue.
        
        Args:
            issue_key: The issue key (e.g., "PLAT-123")
            
        Returns:
            JiraIssue object or None
        """
        response = await self.mcp.call_tool(
            "jira_get_issue",
            {"issue_key": issue_key}
        )
        
        if not response.success:
            logger.error(f"Failed to get issue {issue_key}: {response.error}")
            return None
        
        return JiraIssue.from_dict(response.data)
    
    async def get_epics(
        self,
        project_key: str,
        status: Optional[str] = None,
    ) -> list[JiraIssue]:
        """
        Get epics for a project.
        
        Args:
            project_key: The project key
            status: Optional status filter (e.g., "Done", "In Progress")
            
        Returns:
            List of epic issues
        """
        jql = f'project = "{project_key}" AND issuetype = Epic'
        if status:
            jql += f' AND status = "{status}"'
        jql += " ORDER BY created DESC"
        
        return await self.search_issues(jql)
    
    async def get_stories_for_epic(self, epic_key: str) -> list[JiraIssue]:
        """
        Get all stories linked to an epic.
        
        Args:
            epic_key: The epic key
            
        Returns:
            List of story issues
        """
        jql = f'"Epic Link" = "{epic_key}" ORDER BY created DESC'
        return await self.search_issues(jql)
    
    async def get_technical_debt(
        self,
        project_key: str,
    ) -> list[JiraIssue]:
        """
        Get technical debt issues for a project.
        
        Args:
            project_key: The project key
            
        Returns:
            List of technical debt issues
        """
        # Search for issues labeled as tech debt or of tech debt type
        jql = f'''
            project = "{project_key}" AND (
                labels in (tech-debt, "technical-debt", techdebt) OR
                issuetype = "Technical Debt"
            ) ORDER BY priority DESC
        '''
        return await self.search_issues(jql)
    
    async def get_bugs(
        self,
        project_key: str,
        status: Optional[str] = None,
        component: Optional[str] = None,
    ) -> list[JiraIssue]:
        """
        Get bug issues for a project.
        
        Args:
            project_key: The project key
            status: Optional status filter
            component: Optional component filter
            
        Returns:
            List of bug issues
        """
        jql = f'project = "{project_key}" AND issuetype = Bug'
        if status:
            jql += f' AND status = "{status}"'
        if component:
            jql += f' AND component = "{component}"'
        jql += " ORDER BY priority DESC, created DESC"
        
        return await self.search_issues(jql)
    
    async def get_recent_releases(
        self,
        project_key: str,
        limit: int = 10,
    ) -> list[JiraIssue]:
        """
        Get recently completed issues (for release notes).
        
        Args:
            project_key: The project key
            limit: Maximum number of issues
            
        Returns:
            List of recently resolved issues
        """
        jql = f'''
            project = "{project_key}" AND 
            status = Done AND 
            resolved >= -30d 
            ORDER BY resolved DESC
        '''
        return await self.search_issues(jql, max_results=limit)
    
    async def extract_feature_documentation(
        self,
        project_key: str,
    ) -> list[dict[str, Any]]:
        """
        Extract feature documentation from epics and stories.
        
        Returns structured information about features suitable
        for documentation generation.
        """
        features = []
        
        epics = await self.get_epics(project_key)
        
        for epic in epics:
            stories = await self.get_stories_for_epic(epic.key)
            
            features.append({
                "epic": {
                    "key": epic.key,
                    "summary": epic.summary,
                    "description": epic.description,
                    "status": epic.status,
                },
                "stories": [
                    {
                        "key": s.key,
                        "summary": s.summary,
                        "description": s.description,
                        "status": s.status,
                        "components": s.components,
                    }
                    for s in stories
                ],
                "components": list(set(
                    comp for s in stories for comp in s.components
                )),
            })
        
        return features
