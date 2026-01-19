# Natterbox Platform Documentation

Comprehensive documentation for the Natterbox platform - architecture, services, operations, and onboarding guides.

## 🎯 Purpose

This repository serves as the **source of truth** for technical documentation of the Natterbox platform. It covers:

- **Architecture** - System design, component relationships, data flows
- **Services** - Individual service documentation and inventories
- **Operations** - Runbooks, incident response, deployment procedures
- **Terraform Modules** - Infrastructure as code catalog
- **Onboarding** - Guides for new team members

## 📁 Structure

```
platform-documents/
├── .project/                    # Project tracking (status, backlog, decisions)
├── architecture/                # System architecture documentation
│   ├── voice-routing/          # Core telephony/FreeSWITCH
│   ├── omnichannel/            # Multi-channel communication
│   ├── salesforce-integration/ # CRM integration (AVS, SCV)
│   ├── infrastructure/         # AWS, networking, deployment
│   └── ai-cai/                 # Conversational AI
├── services/                    # Individual service documentation
├── terraform-modules/           # IaC module catalog
├── operations/                  # Operational documentation
│   └── runbooks/               # Step-by-step operational procedures
└── onboarding/                  # New starter guides
```

## 🚀 Quick Links

| Document | Description |
|----------|-------------|
| [Project Status](.project/STATUS.md) | Current progress and state |
| [Backlog](.project/BACKLOG.md) | Prioritized work items |
| [Service Inventory](services/inventory.md) | Master list of all services |
| [Architecture Overview](architecture/overview.md) | High-level system design |

## 🔄 How This Repo Works

This documentation is being developed iteratively with AI assistance. The `.project/` directory tracks:

- **STATUS.md** - Current state, what's in progress
- **BACKLOG.md** - Prioritized list of documentation work
- **COMPLETED.md** - Finished items with dates
- **DECISIONS.md** - Key decisions made during the project
- **QUESTIONS.md** - Open questions needing human input
- **sessions/** - Logs of each working session

## 📊 Project Progress

See [.project/STATUS.md](.project/STATUS.md) for current status.

## 🤝 Contributing

1. Check the [backlog](.project/BACKLOG.md) for priority items
2. Review [decisions](.project/DECISIONS.md) for context on choices made
3. Submit PRs for review
4. Update tracking files when completing work

## 📚 Related Resources

- **Confluence** - [Architecture Space](https://natterbox.atlassian.net/wiki/spaces/A)
- **Confluence** - [Platform Support & Engineering](https://natterbox.atlassian.net/wiki/spaces/CO)
- **Document360** - [Public Documentation](https://docs.natterbox.com)

---

*This documentation project started January 2026*
