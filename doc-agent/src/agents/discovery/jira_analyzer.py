"""Jira Analyzer Agent - extracts technical context from Jira."""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Optional

from ..base import BaseAgent, AgentResult, AgentContext
from ...knowledge import (
    Document,
    Person,
    Relation,
    RelationType,
)
from ...mcp.jira import JiraClient, JiraIssue, JiraComponent

logger = logging.getLogger("doc-agent.agents.discovery.jira_analyzer")


class JiraAnalyzerAgent(BaseAgent):
    """
    Agent that extracts technical context from Jira.
    
    Extracts:
    - Epic and story descriptions (feature documentation)
    - Technical debt items (known limitations)
    - Bug patterns (common issues for troubleshooting)
    - Component definitions and ownership
    - Release notes content
    """
    
    name = "jira_analyzer"
    description = "Extracts technical context and feature information from Jira"
    version = "0.1.0"
    
    def __init__(self, context: AgentContext):
        super().__init__(context)
        self.jira = JiraClient(self.mcp)
        
        # Configuration
        source_config = context.config.get("sources", {}).get("jira", {})
        self.projects = source_config.get("projects", [])
        self.issue_types = source_config.get("issue_types", ["Epic", "Story", "Bug"])
    
    async def run(self) -> AgentResult:
        """Execute the Jira analysis process."""
        self.logger.info(f"Analyzing Jira projects: {self.projects}")
        
        # Load checkpoint for incremental updates
        checkpoint = await self.load_checkpoint()
        processed_issues = set(checkpoint.get("processed_issues", [])) if checkpoint else set()
        
        discovered_features = 0
        discovered_tech_debt = 0
        discovered_owners = 0
        errors = []
        
        for project_key in self.projects:
            try:
                # Extract technical debt
                tech_debt = await self.jira.get_technical_debt(project_key)
                for issue in tech_debt:
                    if issue.key not in processed_issues:
                        doc = await self._process_tech_debt(issue, project_key)
                        if doc:
                            self.graph.add_entity(doc)
                            discovered_tech_debt += 1
                        processed_issues.add(issue.key)
                
                # Extract bug patterns for troubleshooting
                bugs = await self.jira.get_bugs(project_key, status="Done")
                bug_docs = await self._analyze_bug_patterns(bugs, project_key)
                for doc in bug_docs:
                    self.graph.add_entity(doc)
                
            except Exception as e:
                self.logger.error(f"Failed to analyze project {project_key}: {e}")
                errors.append(f"project/{project_key}: {str(e)}")
        
        # Extract feature documentation from all projects at once
        try:
            features = await self.jira.extract_feature_documentation(self.projects)
            for feature in features:
                try:
                    project_key = feature.key.split("-")[0] if feature.key else ""
                    docs = await self._process_feature(feature, project_key)
                    discovered_features += len(docs)
                    for doc in docs:
                        self.graph.add_entity(doc)
                except Exception as e:
                    self.logger.warning(f"Failed to process feature: {e}")
        except Exception as e:
            self.logger.warning(f"Failed to extract feature documentation: {e}")
        
        # Save checkpoint
        await self.save_checkpoint({
            "processed_issues": list(processed_issues),
            "last_run": datetime.utcnow().isoformat(),
        })
        
        self.logger.info(
            f"Jira analysis complete: {discovered_features} features, "
            f"{discovered_tech_debt} tech debt items, {discovered_owners} owners"
        )
        
        return AgentResult(
            success=len(errors) == 0 or discovered_features > 0,
            data={
                "discovered_features": discovered_features,
                "discovered_tech_debt": discovered_tech_debt,
                "discovered_owners": discovered_owners,
            },
            error="; ".join(errors) if errors else None,
            metadata={"projects": self.projects},
        )
    
    async def _process_component(
        self,
        component: JiraComponent,
        project_key: str,
    ) -> Optional[Person]:
        """
        Process a Jira component and extract ownership information.
        """
        if not component.lead:
            return None
        
        # Create or update person entity
        person_id = f"person:{component.lead.lower().replace(' ', '_')}"
        existing = self.graph.get_entity(person_id)
        
        if existing:
            # Update owned services
            if isinstance(existing, Person):
                if component.name not in existing.owned_services:
                    existing.owned_services.append(component.name)
            return None
        
        person = Person(
            id=person_id,
            name=component.lead,
            description=f"Lead for {component.name}",
            owned_services=[component.name],
            metadata={
                "project": project_key,
                "component": component.name,
            },
        )
        self.graph.add_entity(person)
        
        # Link to service if exists
        service_id = f"service:{component.name.lower().replace(' ', '-')}"
        if self.graph.get_entity(service_id):
            self.graph.add_relation(Relation(
                source_id=person_id,
                target_id=service_id,
                relation_type=RelationType.OWNS,
            ))
        
        return person
    
    async def _process_feature(
        self,
        feature: dict[str, Any],
        project_key: str,
    ) -> list[Document]:
        """
        Process a feature (epic with stories) and create documentation entities.
        """
        documents = []
        epic = feature.get("epic", {})
        stories = feature.get("stories", [])
        
        if not epic:
            return documents
        
        # Analyze the feature using Claude
        feature_doc = await self._analyze_feature(epic, stories)
        
        # Create document entity for the feature
        doc = Document(
            id=f"jira:feature:{epic['key']}",
            name=epic.get("summary", "Unknown Feature"),
            description=feature_doc.get("summary"),
            source_type="jira",
            url=f"https://jira.example.com/browse/{epic['key']}",  # Will be replaced with actual URL
            content=json.dumps({
                "epic": epic,
                "stories": stories,
                "analysis": feature_doc,
            }),
            labels=["feature", project_key],
            linked_services=feature.get("components", []),
            metadata={
                "project": project_key,
                "epic_key": epic["key"],
                "story_count": len(stories),
                "status": epic.get("status"),
                "capabilities": feature_doc.get("capabilities", []),
                "user_value": feature_doc.get("user_value"),
            },
        )
        documents.append(doc)
        
        # Link to services
        for component in feature.get("components", []):
            service_id = f"service:{component.lower().replace(' ', '-')}"
            if self.graph.get_entity(service_id):
                self.graph.add_relation(Relation(
                    source_id=doc.id,
                    target_id=service_id,
                    relation_type=RelationType.DOCUMENTS,
                ))
        
        return documents
    
    async def _analyze_feature(
        self,
        epic: dict[str, Any],
        stories: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Use Claude to analyze a feature and extract documentation-worthy information.
        """
        # Build context
        story_summaries = "\n".join([
            f"- {s.get('summary', 'Unknown')} ({s.get('status', 'Unknown')})"
            for s in stories[:10]  # Limit to first 10
        ])
        
        prompt = f"""Analyze this feature from Jira and extract documentation-worthy information.

Epic: {epic.get('summary', 'Unknown')}
Description: {epic.get('description', 'No description')}
Status: {epic.get('status', 'Unknown')}

Stories in this epic:
{story_summaries}

Extract the following in JSON format:
{{
    "summary": "2-3 sentence summary of what this feature provides",
    "capabilities": ["list", "of", "capabilities", "this", "feature", "enables"],
    "user_value": "one sentence describing the value to users",
    "technical_notes": "any technical implementation notes worth documenting",
    "is_complete": true/false based on epic status
}}

Focus on what the feature does for users, not implementation details.
Return ONLY valid JSON, no additional text."""
        
        try:
            response = await self.call_claude(
                system_prompt=self.get_system_prompt(),
                user_message=prompt,
                temperature=0.2,
            )
            
            # Parse JSON response
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            
            return json.loads(response)
            
        except Exception as e:
            self.logger.warning(f"Failed to analyze feature with Claude: {e}")
            return {
                "summary": epic.get("summary", ""),
                "capabilities": [],
            }
    
    async def _process_tech_debt(
        self,
        issue: JiraIssue,
        project_key: str,
    ) -> Optional[Document]:
        """
        Process a technical debt issue and create a documentation entity.
        """
        if not issue.description:
            return None
        
        doc = Document(
            id=f"jira:techdebt:{issue.key}",
            name=issue.summary,
            description=f"Technical debt: {issue.summary}",
            source_type="jira",
            url=issue.url,
            content=issue.description,
            labels=["tech-debt", project_key] + issue.labels,
            linked_services=issue.components,
            metadata={
                "project": project_key,
                "issue_key": issue.key,
                "status": issue.status,
                "priority": issue.priority,
                "components": issue.components,
            },
        )
        
        return doc
    
    async def _analyze_bug_patterns(
        self,
        bugs: list[JiraIssue],
        project_key: str,
    ) -> list[Document]:
        """
        Analyze resolved bugs to identify common patterns for troubleshooting.
        """
        if not bugs:
            return []
        
        # Group bugs by component
        by_component: dict[str, list[JiraIssue]] = {}
        for bug in bugs:
            for component in bug.components or ["General"]:
                if component not in by_component:
                    by_component[component] = []
                by_component[component].append(bug)
        
        documents = []
        
        for component, component_bugs in by_component.items():
            if len(component_bugs) < 3:
                continue  # Need enough bugs to identify patterns
            
            # Analyze patterns using Claude
            patterns = await self._identify_bug_patterns(component, component_bugs)
            
            if patterns.get("patterns"):
                doc = Document(
                    id=f"jira:bugpatterns:{project_key}:{component.lower().replace(' ', '-')}",
                    name=f"Common Issues: {component}",
                    description=f"Common issues and troubleshooting for {component}",
                    source_type="jira",
                    url=f"https://jira.example.com/issues/?jql=project={project_key}",
                    content=json.dumps(patterns),
                    labels=["troubleshooting", "bugs", project_key],
                    linked_services=[component],
                    metadata={
                        "project": project_key,
                        "component": component,
                        "bug_count": len(component_bugs),
                        "patterns": patterns.get("patterns", []),
                    },
                )
                documents.append(doc)
        
        return documents
    
    async def _identify_bug_patterns(
        self,
        component: str,
        bugs: list[JiraIssue],
    ) -> dict[str, Any]:
        """
        Use Claude to identify common bug patterns from resolved issues.
        """
        bug_summaries = "\n".join([
            f"- {b.summary} (Priority: {b.priority})"
            for b in bugs[:20]  # Limit to 20 bugs
        ])
        
        prompt = f"""Analyze these resolved bugs for the {component} component and identify common patterns.

Bugs:
{bug_summaries}

Extract the following in JSON format:
{{
    "patterns": [
        {{
            "name": "pattern name",
            "description": "what causes this issue",
            "symptoms": ["how", "to", "identify"],
            "resolution": "how to fix or work around"
        }}
    ],
    "common_causes": ["list", "of", "common", "root", "causes"],
    "troubleshooting_tips": ["general", "tips", "for", "debugging"]
}}

Focus on actionable patterns that would help someone troubleshoot similar issues.
Return ONLY valid JSON, no additional text."""
        
        try:
            response = await self.call_claude(
                system_prompt=self.get_system_prompt(),
                user_message=prompt,
                temperature=0.2,
            )
            
            # Parse JSON response
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            
            return json.loads(response)
            
        except Exception as e:
            self.logger.warning(f"Failed to identify bug patterns with Claude: {e}")
            return {
                "patterns": [],
                "common_causes": [],
                "troubleshooting_tips": [],
            }
    
    def get_system_prompt(self) -> str:
        return """You are a technical documentation agent analyzing Jira issues.

Your role is to:
1. Extract documentation-worthy information from features and epics
2. Identify patterns in bugs that can help with troubleshooting
3. Understand technical debt and its implications
4. Focus on user value and practical information

Be concise but comprehensive. Focus on information that would help:
- New developers understand features
- Support teams troubleshoot issues
- Teams prioritize technical work

Return structured JSON that can be used to generate documentation."""
