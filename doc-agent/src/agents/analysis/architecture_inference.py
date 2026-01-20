"""Architecture Inference Agent - analyzes data to infer system architecture."""

import asyncio
import json
import logging
from typing import Any, Optional
from collections import defaultdict

from ..base import BaseAgent, AgentResult, AgentContext
from ...knowledge import (
    Service,
    Domain,
    API,
    Schema,
    Relation,
    RelationType,
    EntityType,
)

logger = logging.getLogger("doc-agent.agents.analysis.architecture_inference")


class ArchitectureInferenceAgent(BaseAgent):
    """
    Agent that analyzes discovered data to infer system architecture.
    
    Capabilities:
    - Identify service boundaries and responsibilities
    - Detect communication patterns (sync/async, protocols)
    - Map data flows between services
    - Identify shared databases and coupling points
    - Classify services by type (API, worker, etc.)
    """
    
    name = "architecture_inference"
    description = "Analyzes discovered data to infer system architecture"
    version = "0.1.0"
    
    async def run(self) -> AgentResult:
        """Execute the architecture inference process."""
        self.logger.info("Starting architecture inference")
        
        services = self.graph.get_services()
        
        if not services:
            self.logger.warning("No services found in knowledge graph")
            return AgentResult(
                success=True,
                data={"message": "No services to analyze"},
            )
        
        self.logger.info(f"Analyzing architecture for {len(services)} services")
        
        # Step 1: Classify services by type
        await self._classify_services(services)
        
        # Step 2: Infer service dependencies from various sources
        await self._infer_dependencies(services)
        
        # Step 3: Identify communication patterns
        patterns = await self._identify_communication_patterns(services)
        
        # Step 4: Detect shared resources (databases, queues, etc.)
        shared_resources = await self._detect_shared_resources(services)
        
        # Step 5: Generate architecture summary using Claude
        summary = await self._generate_architecture_summary(
            services, patterns, shared_resources
        )
        
        # Store architecture metadata
        self.graph.add_entity(Schema(
            id="architecture:metadata",
            name="Architecture Metadata",
            description="Inferred architecture information",
            schema_type="metadata",
            definition=summary,
            metadata={
                "service_count": len(services),
                "patterns": patterns,
                "shared_resources": shared_resources,
            },
        ))
        
        self.logger.info("Architecture inference complete")
        
        return AgentResult(
            success=True,
            data={
                "services_analyzed": len(services),
                "patterns_identified": len(patterns),
                "shared_resources": len(shared_resources),
                "summary": summary,
            },
        )
    
    async def _classify_services(self, services: list[Service]) -> None:
        """
        Classify services by their type and role in the architecture.
        """
        for service in services:
            service_type = await self._infer_service_type(service)
            
            # Update service metadata
            service.metadata["service_type"] = service_type
            service.metadata["is_api_gateway"] = service_type == "api_gateway"
            service.metadata["is_worker"] = service_type in ("worker", "consumer")
            service.metadata["is_core"] = service_type in ("core", "platform")
            
            self.logger.debug(f"Classified {service.name} as {service_type}")
    
    async def _infer_service_type(self, service: Service) -> str:
        """
        Infer the type of a service based on its characteristics.
        """
        name_lower = service.name.lower()
        
        # Check naming patterns
        if any(x in name_lower for x in ["gateway", "proxy", "router"]):
            return "api_gateway"
        if any(x in name_lower for x in ["worker", "processor", "handler", "job"]):
            return "worker"
        if any(x in name_lower for x in ["consumer", "subscriber", "listener"]):
            return "consumer"
        if any(x in name_lower for x in ["scheduler", "cron"]):
            return "scheduler"
        if any(x in name_lower for x in ["api", "service", "backend"]):
            return "api_service"
        if any(x in name_lower for x in ["ui", "frontend", "web", "dashboard"]):
            return "frontend"
        if any(x in name_lower for x in ["db", "database", "store"]):
            return "data_store"
        if any(x in name_lower for x in ["auth", "identity", "iam"]):
            return "auth"
        if any(x in name_lower for x in ["notification", "email", "sms"]):
            return "notification"
        if any(x in name_lower for x in ["analytics", "metrics", "monitoring"]):
            return "observability"
        
        # Check for APIs
        apis = self.graph.get_service_apis(service.id)
        if apis:
            return "api_service"
        
        # Default
        return "service"
    
    async def _infer_dependencies(self, services: list[Service]) -> None:
        """
        Infer service dependencies from multiple sources.
        """
        # Get existing dependencies from discovery
        for service in services:
            # Check package dependencies
            for dep_name in service.dependencies:
                # Try to match to a known service
                for other_service in services:
                    if other_service.id == service.id:
                        continue
                    
                    # Match by name similarity
                    if self._names_match(dep_name, other_service.name):
                        # Create dependency relation if not exists
                        existing = self.graph.get_relations(
                            source_id=service.id,
                            target_id=other_service.id,
                            relation_type=RelationType.DEPENDS_ON,
                        )
                        if not existing:
                            self.graph.add_relation(Relation(
                                source_id=service.id,
                                target_id=other_service.id,
                                relation_type=RelationType.DEPENDS_ON,
                                metadata={"source": "package_dependency"},
                            ))
        
        # Infer dependencies from API calls (if we have that info)
        for service in services:
            apis = self.graph.get_service_apis(service.id)
            for api in apis:
                # Check if any other service references this API
                for other_service in services:
                    if other_service.id == service.id:
                        continue
                    
                    # Check if other service's description mentions this API
                    if service.name.lower() in (other_service.description or "").lower():
                        existing = self.graph.get_relations(
                            source_id=other_service.id,
                            target_id=service.id,
                            relation_type=RelationType.CALLS,
                        )
                        if not existing:
                            self.graph.add_relation(Relation(
                                source_id=other_service.id,
                                target_id=service.id,
                                relation_type=RelationType.CALLS,
                                metadata={"source": "inferred_from_description"},
                            ))
    
    async def _identify_communication_patterns(
        self,
        services: list[Service],
    ) -> list[dict[str, Any]]:
        """
        Identify communication patterns between services.
        """
        patterns = []
        
        # Count API types
        api_types: dict[str, int] = defaultdict(int)
        for service in services:
            apis = self.graph.get_service_apis(service.id)
            for api in apis:
                api_types[api.api_type] += 1
        
        if api_types:
            patterns.append({
                "name": "API Communication",
                "description": "Services communicate via APIs",
                "types": dict(api_types),
            })
        
        # Check for async patterns (queue/event-based)
        async_services = [
            s for s in services
            if any(x in s.name.lower() for x in ["queue", "event", "kafka", "rabbit", "sqs"])
        ]
        if async_services:
            patterns.append({
                "name": "Async Messaging",
                "description": "Asynchronous communication via message queues",
                "services": [s.name for s in async_services],
            })
        
        # Check for database access patterns
        db_services = [
            s for s in services
            if s.databases or any(x in s.name.lower() for x in ["db", "postgres", "mysql", "mongo"])
        ]
        if db_services:
            patterns.append({
                "name": "Database Access",
                "description": "Direct database access pattern",
                "services": [s.name for s in db_services],
            })
        
        return patterns
    
    async def _detect_shared_resources(
        self,
        services: list[Service],
    ) -> list[dict[str, Any]]:
        """
        Detect shared resources between services.
        """
        shared_resources = []
        
        # Check for shared databases
        db_usage: dict[str, list[str]] = defaultdict(list)
        for service in services:
            for db in service.databases:
                db_usage[db].append(service.name)
        
        for db, using_services in db_usage.items():
            if len(using_services) > 1:
                shared_resources.append({
                    "type": "database",
                    "name": db,
                    "services": using_services,
                    "risk": "coupling" if len(using_services) > 3 else "low",
                })
        
        # Check for shared dependencies
        dep_usage: dict[str, list[str]] = defaultdict(list)
        for service in services:
            for dep in service.dependencies:
                # Focus on internal dependencies
                if "natterbox" in dep.lower() or "internal" in dep.lower():
                    dep_usage[dep].append(service.name)
        
        for dep, using_services in dep_usage.items():
            if len(using_services) > 2:
                shared_resources.append({
                    "type": "shared_library",
                    "name": dep,
                    "services": using_services,
                })
        
        return shared_resources
    
    async def _generate_architecture_summary(
        self,
        services: list[Service],
        patterns: list[dict[str, Any]],
        shared_resources: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Generate a high-level architecture summary using Claude.
        """
        # Build context for Claude
        service_list = "\n".join([
            f"- {s.name}: {s.description or 'No description'} "
            f"(type: {s.metadata.get('service_type', 'unknown')}, "
            f"language: {s.language or 'unknown'})"
            for s in services[:30]  # Limit to 30 services
        ])
        
        patterns_text = "\n".join([
            f"- {p['name']}: {p['description']}"
            for p in patterns
        ])
        
        shared_text = "\n".join([
            f"- {r['type']}: {r['name']} (used by: {', '.join(r['services'][:5])})"
            for r in shared_resources[:10]
        ])
        
        prompt = f"""Analyze this platform architecture and provide a high-level summary.

Services ({len(services)} total):
{service_list}

Communication Patterns:
{patterns_text if patterns_text else 'None identified'}

Shared Resources:
{shared_text if shared_text else 'None identified'}

Provide a JSON summary with:
{{
    "overview": "2-3 paragraph description of the overall architecture",
    "key_characteristics": ["list", "of", "key", "architectural", "characteristics"],
    "architecture_style": "microservices/monolithic/modular/hybrid",
    "strengths": ["architectural", "strengths"],
    "areas_of_concern": ["potential", "issues", "or", "complexity"],
    "technology_stack": {{
        "languages": ["primary", "languages"],
        "frameworks": ["key", "frameworks"],
        "infrastructure": ["infrastructure", "components"]
    }},
    "recommended_documentation_focus": ["areas", "to", "document", "thoroughly"]
}}

Return ONLY valid JSON, no additional text."""
        
        try:
            response = await self.call_claude(
                system_prompt=self.get_system_prompt(),
                user_message=prompt,
                temperature=0.3,
            )
            
            # Parse JSON response
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            
            return json.loads(response)
            
        except Exception as e:
            self.logger.warning(f"Failed to generate architecture summary: {e}")
            return {
                "overview": f"Platform with {len(services)} services",
                "architecture_style": "microservices",
            }
    
    def _names_match(self, name1: str, name2: str) -> bool:
        """Check if two names likely refer to the same thing."""
        # Normalize names
        n1 = name1.lower().replace("-", "").replace("_", "").replace("@natterbox/", "")
        n2 = name2.lower().replace("-", "").replace("_", "")
        
        return n1 == n2 or n1 in n2 or n2 in n1
    
    def get_system_prompt(self) -> str:
        return """You are a software architecture analyst.

Your role is to:
1. Understand system architectures from service descriptions
2. Identify patterns, strengths, and concerns
3. Provide actionable insights for documentation

Be objective and technical. Base your analysis only on the provided information.
When uncertain, note the uncertainty rather than guessing.
Focus on insights that would help someone understand and document the system."""
