"""Domain Mapper Agent - organizes services into logical domains."""

import asyncio
import json
import logging
from typing import Any, Optional
from collections import defaultdict

from ..base import BaseAgent, AgentResult, AgentContext
from ...knowledge import (
    Service,
    Domain,
    Relation,
    RelationType,
)

logger = logging.getLogger("doc-agent.agents.analysis.domain_mapper")


class DomainMapperAgent(BaseAgent):
    """
    Agent that organizes services into logical domains.
    
    Capabilities:
    - Cluster related services based on naming, dependencies, and function
    - Propose domain hierarchy
    - Identify cross-cutting concerns
    - Map domain interactions
    """
    
    name = "domain_mapper"
    description = "Organizes services into logical domains based on function and relationships"
    version = "0.1.0"
    
    # Common domain patterns to look for
    DOMAIN_PATTERNS = {
        "voice": ["voice", "call", "phone", "sip", "freeswitch", "telephony", "pbx", "ivr"],
        "billing": ["billing", "invoice", "payment", "subscription", "charge", "price"],
        "integration": ["integration", "salesforce", "teams", "crm", "connector", "sync"],
        "platform": ["platform", "core", "common", "shared", "base", "foundation"],
        "auth": ["auth", "identity", "user", "permission", "role", "security", "oauth"],
        "analytics": ["analytics", "report", "metric", "dashboard", "insight", "stats"],
        "notification": ["notification", "email", "sms", "alert", "message", "push"],
        "infrastructure": ["infra", "deploy", "ci", "cd", "terraform", "kubernetes", "k8s"],
        "data": ["data", "etl", "pipeline", "warehouse", "lake", "sync"],
        "api": ["api", "gateway", "proxy", "router", "graphql"],
    }
    
    async def run(self) -> AgentResult:
        """Execute the domain mapping process."""
        self.logger.info("Starting domain mapping")
        
        services = self.graph.get_services()
        
        if not services:
            self.logger.warning("No services found in knowledge graph")
            return AgentResult(
                success=True,
                data={"message": "No services to map"},
            )
        
        self.logger.info(f"Mapping domains for {len(services)} services")
        
        # Step 1: Initial clustering based on naming patterns
        clusters = self._cluster_by_name(services)
        
        # Step 2: Refine clusters using Claude
        refined_domains = await self._refine_domains_with_ai(services, clusters)
        
        # Step 3: Create domain entities
        created_domains = []
        for domain_data in refined_domains:
            domain = Domain(
                id=f"domain:{domain_data['id']}",
                name=domain_data["name"],
                description=domain_data.get("description"),
                services=[s["id"] for s in domain_data.get("services", [])],
                metadata={
                    "responsibilities": domain_data.get("responsibilities", []),
                    "key_technologies": domain_data.get("key_technologies", []),
                },
            )
            self.graph.add_entity(domain)
            created_domains.append(domain)
            
            # Create relationships between domain and services
            for service_id in domain.services:
                self.graph.add_relation(Relation(
                    source_id=service_id,
                    target_id=domain.id,
                    relation_type=RelationType.BELONGS_TO,
                ))
        
        # Step 4: Identify domain interactions
        interactions = await self._identify_domain_interactions(created_domains)
        
        # Step 5: Identify cross-cutting concerns
        cross_cutting = await self._identify_cross_cutting_concerns(services, created_domains)
        
        self.logger.info(
            f"Domain mapping complete: {len(created_domains)} domains, "
            f"{len(interactions)} interactions"
        )
        
        return AgentResult(
            success=True,
            data={
                "domains_created": len(created_domains),
                "domain_names": [d.name for d in created_domains],
                "interactions": interactions,
                "cross_cutting_concerns": cross_cutting,
            },
        )
    
    def _cluster_by_name(self, services: list[Service]) -> dict[str, list[Service]]:
        """
        Initial clustering of services based on naming patterns.
        """
        clusters: dict[str, list[Service]] = defaultdict(list)
        unclustered: list[Service] = []
        
        for service in services:
            name_lower = service.name.lower()
            description_lower = (service.description or "").lower()
            
            matched = False
            for domain_name, patterns in self.DOMAIN_PATTERNS.items():
                if any(p in name_lower or p in description_lower for p in patterns):
                    clusters[domain_name].append(service)
                    matched = True
                    break
            
            if not matched:
                unclustered.append(service)
        
        # Add unclustered to "other"
        if unclustered:
            clusters["other"] = unclustered
        
        return dict(clusters)
    
    async def _refine_domains_with_ai(
        self,
        services: list[Service],
        initial_clusters: dict[str, list[Service]],
    ) -> list[dict[str, Any]]:
        """
        Use Claude to refine domain assignments and provide descriptions.
        """
        # Build context for Claude
        cluster_info = []
        for domain_name, domain_services in initial_clusters.items():
            cluster_info.append({
                "suggested_domain": domain_name,
                "services": [
                    {
                        "id": s.id,
                        "name": s.name,
                        "description": s.description,
                        "type": s.metadata.get("service_type", "unknown"),
                    }
                    for s in domain_services
                ],
            })
        
        prompt = f"""Analyze these service clusters and refine the domain organization.

Initial Clusters:
{json.dumps(cluster_info, indent=2)}

Review and refine these domains. For each domain, provide:
1. A clear, business-oriented name (not just technical)
2. A description of what the domain is responsible for
3. Confirm or adjust which services belong
4. List key responsibilities

Return JSON array:
[
    {{
        "id": "domain-slug",
        "name": "Human Readable Domain Name",
        "description": "2-3 sentence description of domain purpose",
        "services": [
            {{"id": "service:name", "name": "service-name", "fit_reason": "why it belongs"}}
        ],
        "responsibilities": ["list", "of", "domain", "responsibilities"],
        "key_technologies": ["primary", "technologies"],
        "interactions": ["other", "domains", "this", "interacts", "with"]
    }}
]

Rules:
- Combine very small domains (1-2 services) into related larger domains
- Split "other" into meaningful domains if possible
- Each service should belong to exactly one domain
- Use business terminology, not just technical names

Return ONLY valid JSON array, no additional text."""
        
        try:
            response = await self.call_claude(
                system_prompt=self.get_system_prompt(),
                user_message=prompt,
                temperature=0.3,
                max_tokens=4096,
            )
            
            # Parse JSON response
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            
            domains = json.loads(response)
            return domains
            
        except Exception as e:
            self.logger.warning(f"Failed to refine domains with Claude: {e}")
            # Fall back to initial clusters
            return [
                {
                    "id": name,
                    "name": name.replace("_", " ").title(),
                    "description": f"Services related to {name}",
                    "services": [
                        {"id": s.id, "name": s.name}
                        for s in services
                    ],
                    "responsibilities": [],
                }
                for name, services in initial_clusters.items()
            ]
    
    async def _identify_domain_interactions(
        self,
        domains: list[Domain],
    ) -> list[dict[str, Any]]:
        """
        Identify how domains interact with each other.
        """
        interactions = []
        
        for domain in domains:
            for service_id in domain.services:
                # Get services this one depends on
                deps = self.graph.get_related_entities(
                    service_id,
                    RelationType.DEPENDS_ON,
                    direction="outgoing",
                )
                
                for dep in deps:
                    if not isinstance(dep, Service):
                        continue
                    
                    # Find which domain the dependency belongs to
                    dep_domain = None
                    for other_domain in domains:
                        if dep.id in other_domain.services:
                            dep_domain = other_domain
                            break
                    
                    if dep_domain and dep_domain.id != domain.id:
                        # Record interaction
                        interaction_key = f"{domain.id}->{dep_domain.id}"
                        existing = [i for i in interactions if i.get("key") == interaction_key]
                        
                        if existing:
                            existing[0]["services"].append({
                                "from": service_id,
                                "to": dep.id,
                            })
                        else:
                            interactions.append({
                                "key": interaction_key,
                                "from_domain": domain.name,
                                "to_domain": dep_domain.name,
                                "services": [{
                                    "from": service_id,
                                    "to": dep.id,
                                }],
                            })
        
        # Create domain-level relations
        for interaction in interactions:
            from_domain_id = f"domain:{interaction['key'].split('->')[0]}"
            to_domain_id = f"domain:{interaction['key'].split('->')[1]}"
            
            self.graph.add_relation(Relation(
                source_id=from_domain_id,
                target_id=to_domain_id,
                relation_type=RelationType.DEPENDS_ON,
                metadata={
                    "service_connections": len(interaction["services"]),
                },
            ))
        
        return interactions
    
    async def _identify_cross_cutting_concerns(
        self,
        services: list[Service],
        domains: list[Domain],
    ) -> list[dict[str, Any]]:
        """
        Identify cross-cutting concerns that span multiple domains.
        """
        concerns = []
        
        # Look for services/libraries used across multiple domains
        # Common patterns: logging, auth, config, etc.
        
        cross_cutting_patterns = {
            "logging": ["log", "logging", "logger"],
            "authentication": ["auth", "jwt", "oauth", "token"],
            "configuration": ["config", "settings", "env"],
            "monitoring": ["monitor", "metric", "trace", "health"],
            "error_handling": ["error", "exception", "handler"],
        }
        
        for concern_name, patterns in cross_cutting_patterns.items():
            affected_domains = set()
            affected_services = []
            
            for service in services:
                deps_lower = [d.lower() for d in service.dependencies]
                
                if any(p in d for p in patterns for d in deps_lower):
                    # Find which domain this service belongs to
                    for domain in domains:
                        if service.id in domain.services:
                            affected_domains.add(domain.name)
                            affected_services.append(service.name)
                            break
            
            if len(affected_domains) > 1:
                concerns.append({
                    "name": concern_name.replace("_", " ").title(),
                    "affected_domains": list(affected_domains),
                    "affected_services_count": len(affected_services),
                    "description": f"Cross-cutting concern spanning {len(affected_domains)} domains",
                })
        
        return concerns
    
    def get_system_prompt(self) -> str:
        return """You are a domain-driven design expert analyzing a software platform.

Your role is to:
1. Organize services into logical, cohesive domains
2. Identify clear boundaries and responsibilities
3. Use business-oriented naming and descriptions
4. Ensure each service belongs to exactly one domain

Principles:
- Domains should be cohesive (services within work together)
- Domains should be loosely coupled (minimal dependencies between domains)
- Names should be understandable by non-technical stakeholders
- Descriptions should explain the business purpose, not just technical function

Return well-structured JSON that clearly defines the domain organization."""
