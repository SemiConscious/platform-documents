# Deployment Procedures Runbook

**Last Updated:** 2026-01-20  
**Source:** [Confluence - Release Types and Procedures](https://natterbox.atlassian.net/wiki/spaces/ReleaseManagement/pages/2694119427/Release+Types+and+Procedures)

---

## Overview

This runbook covers deployment procedures for the Natterbox platform, including scheduled releases, emergency releases, and CAI (Conversational AI) releases.

---

## Release Types Summary

| Type | Frequency | Maintenance Mode | Process Owner |
|------|-----------|------------------|---------------|
| Product (Bi-Weekly) | Every 2 weeks | Required for RT | QA + PE |
| Platform (Weekly) | Weekly | Required for RT | Platform Engineering |
| Emergency | As needed | Varies | On-call PE |
| CAI | As needed | Limited packages | CAI Team + PE |

---

## Product Release Timeline (Bi-Weekly)

### Gate 1: Git Finish
**Deadline:** 2nd Wednesday of sprint, 17:00 GMT

| Task | Owner |
|------|-------|
| Developer git finishes changes after testing | Dev |
| QA creates HO and links Bug/Story tickets | QA |
| Updates package table with diff & versions | QA |
| Dev advises QA of Special Instructions | Dev |
| Dev deploys change to all QA environments | Dev |

### Gate 2: Assign CR to PE
**Deadline:** 2nd Thursday of sprint, 15:00 GMT

| Task | Owner |
|------|-------|
| QA moves HO to "HO Peer Review" status | QA |
| QA tests functionality on QA envs | QA |
| Note any issues/additional steps on HO | QA |
| QA moves HO to "Ready for P.E Review" status | QA |
| Release Manager updates CR to "Awaiting P.E Instructions" | Release Manager |

### Gate 3: PE Stage Rollout
**Deadline:** 2nd Friday of sprint, 15:00 GMT

| Task | Owner |
|------|-------|
| PE reviews all HOs, clarifying issues | PE |
| PE writes Stage CR Instructions | PE |
| 2nd PE reviews instructions | PE |
| CRs brought to CCB meeting (11:15 GMT Friday) | All |
| PE performs Stage rollout | PE |
| Marks Stage CR as "Released to Stage" | PE |

### Gate 4: Prod CR Ready
**Deadline:** 1st Tuesday post-sprint, 10:00 GMT

| Task | Owner |
|------|-------|
| QA tests on staging environment | QA |
| Feature functionality, regression, sanity testing | QA |
| QA updates HOs to "Ready for Production" | QA |
| Release Manager transitions CR to "Awaiting PE Instructions" | Release Manager |

### Gate 5: Production Rollout Complete
**Deadline:** 1st Friday post-sprint, 10:00 GMT

| Task | Owner | Time |
|------|-------|------|
| PE writes Production CR instructions | PE | Pre-rollout |
| 2nd PE reviews instructions | PE | Pre-rollout |
| Deploy SDC / LON changes | PE | ~11:00 GMT |
| Deploy first EU region changes | PE | ~18:00 GMT |
| QA post-rollout testing (if required) | QA | After EU deploy |
| Final check-versions | PE | Friday 09:00 GMT |
| Mark CR as "Rollout Complete" | PE | Friday 09:00 GMT |

---

## Platform Release Timeline (Weekly)

Platform releases follow similar steps but on a weekly basis instead of bi-weekly.

| Gate | Deadline | Key Activities |
|------|----------|----------------|
| 1 - Assign CR to PE | Thursday 15:00 GMT | HO prep, testing, ready for review |
| 2 - Stage Rollout | Friday 15:00 GMT | PE review, CCB approval, deploy |
| 3 - Prod CR Ready | Tuesday 10:00 GMT | Stage testing complete |
| 4 - Rollout Complete | Friday 10:00 GMT | Production deployment |

---

## Emergency Releases

Emergency releases follow accelerated timelines due to urgency.

### Approval Process

1. Fill out the [Emergency Release Form](https://docs.google.com/forms/d/1_oeCx3Fuk-MTvoD_xMrPpsx-8tz9A8EsjjgveSnGnsU/viewform?edit_requested=true)
2. Consult with the on-call Platform Engineer
3. Raise in `#rm-netops` Slack channel for visibility

### Regional Timing Guidelines

Align RT component releases with out-of-hours periods (Maintenance Mode required):

| Region | Recommended Time |
|--------|-----------------|
| USE2 / USW2 | Before 14:00 GMT |
| APSE1 / APSE2 | Around 12:00 GMT |
| EUW2 / EUC1 | After 18:00 GMT |
| S01 / S02 / LON / Global Platform / Nexus | Any time |

**Note:** LON-based components can impact internal operations. Consider timing carefully.

---

## CAI Releases

CAI releases follow emergency release format but don't require the emergency release form.

### CAI-Eligible Packages (Deploy Any Time)

| Package | Maintenance Mode |
|---------|------------------|
| terraform-bedrock | Not required |
| terraform-cai-territory-setup | Not required |
| terraform-cai | Not required |
| terraform-rt-cai-websocket | Not required |

### CAI-Eligible Packages (Friday Afternoon Only)

| Package |
|---------|
| OMNI settings |
| Avsapp-scripts |
| routing policies |

### Packages Requiring Scheduled Release

These require Maintenance Mode:

| Package |
|---------|
| terraform-rt-deepgram |
| terraform-fsx8 |
| terraform-rt-transcribed |
| fsxinetd8 |
| transcribed |
| stats-transcribed |
| container-noisereduction-transcribed |
| container-turndetect-transcribed |

---

## Failed Handover Actions

### HO Not Ready by Cutoff

If a handover is not ready for PE review by **15:00 Thursday**:
- It will be removed from the release by Release Manager
- Can be added to next week's release once corrected

### HO Fails PE Review

Reasons for failure:

- Versions incorrect/missing
- Packages not deployed to QA (red during RMHT verify-handover)
- No runbooks for listed package
- Invalid special instructions
- New package without rollback instructions

**Resolution:** HO will be pulled from release. Can be added to next week's release once corrected.

### Failed on Stage

**Deployment Failure:**
- Entire handover will be rolled back
- All packages in a handover are assumed interdependent
- Terraform/deployment error outputs provided in HO comments
- HO moved to "Stage Rollback Required" → "Failed Stage Rollout"
- Unlinked from production release
- Re-use HO for future release after fixing

**Testing Failure:**
- All packages in handover rolled back
- QA provides issue details in ticket
- Inform on-call engineer
- Unlinked from production release
- Re-use HO for future release

### Failed on Production

**Deployment Failure:**
- Entire handover rolled back **on both Production and Stage**
- Error outputs provided in HO comments
- HO moved to "Production Rollback Required" → "Stage Rollback Required" → "Failed Production Rollout"

**Testing Failure:**
- All packages in handover rolled back
- QA must inform on-call engineer ASAP
- Provide issue details in ticket

---

## Handover Requirements

For detailed handover requirements, see:
- [Handover Requirements and Guidelines](https://natterbox.atlassian.net/wiki/spaces/ReleaseManagement/pages/2021589005/Handover+Requirements+and+Guidelines)
- [Change Request Requirements and Guidelines](https://natterbox.atlassian.net/wiki/spaces/ReleaseManagement/pages/XXXX/Change+Request+Requirements+and+Guidelines)

### Essential HO Contents

1. **Package Table**
   - Package name
   - Current version
   - New version
   - Diff link

2. **Linked Tickets**
   - Bug/Story Jira tickets

3. **Special Instructions**
   - Pre-deployment steps
   - Post-deployment steps
   - SQL commands (with proper permissions)

4. **Rollback Instructions**
   - Required for new packages
   - Step-by-step rollback procedure

---

## Deployment Commands Reference

### RMHT (Release Management Handover Tool)

```bash
# Verify handover packages deployed to environment
rmht verify-handover <HO-ID>

# Check package versions across all regions
rmht check-versions <package-name>
```

### Maintenance Mode

```bash
# Enable maintenance mode for a region
# (Redirects traffic to sibling region)
# Consult PE documentation for specific commands
```

---

## Related Documentation

- [Emergency Response Runbook](/operations/runbooks/emergency-response.md)
- [Monitoring and Alerting](/operations/runbooks/monitoring-alerting.md)
- [Post Rollout Cheat Sheet](https://natterbox.atlassian.net/wiki/spaces/ENG/pages/1748762630/Post+Rollout+Cheat+Sheet)
- [Finishing Up A Ticket Guide](https://natterbox.atlassian.net/wiki/spaces/ENG/pages/2556002313/Finishing+Up+A+Ticket+Guide)
