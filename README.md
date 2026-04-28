# Azure Cost Governance Platform

![Azure](https://img.shields.io/badge/Azure-Cost_Governance-0078D4?logo=microsoft-azure)
![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![Status](https://img.shields.io/badge/Status-In_Progress-yellow)

## Live Dashboard
🌐 https://stcostdashboard6431.z13.web.core.windows.net

## Problem
Companies move to the cloud expecting savings but receive
unexpected bills with no visibility, no automation, and no
accountability over who is spending what.

## Solution
A serverless Azure cost intelligence platform with:
- Real-time cost visibility across all Azure services
- Automated budget alerts at 50%, 80%, 100%
- Anomaly detection using 7-day rolling average
- Auto-remediation workflows via Logic Apps
- Cost ownership tracking via Azure Policy tagging

## Architecture
```
Azure Cost Management API
        ↓
Azure Functions (Python) → Blob Storage (cache)
        ↓
Log Analytics (KQL queries)
        ↓
Azure Monitor → Logic Apps (auto-remediation)
        ↓
Static Web Dashboard
```

## Tech Stack
- Azure Cost Management API
- Azure Functions (Python 3.11)
- Azure Blob Storage
- Log Analytics Workspace + KQL
- Azure Monitor
- Azure Logic Apps
- Azure Static Web App
- Managed Identity (zero credential storage)

## Progress
- [x] Phase 1 — Foundation, Budget Alerts, Logic Apps, Dashboard
- [x] Phase 2 — Azure Functions, Real Cost Data, Log Analytics, KQL
- [x] Phase 3 — Anomaly Detection deployed and working
- [ ] Phase 4 — Auto-Remediation + Tagging Policy
- [ ] Phase 5 — Portfolio Polish

## Resume Bullet
Built a serverless Azure cost governance platform with automated
anomaly detection and remediation across Azure subscriptions.
Implemented caching and Managed Identity authentication for
secure, high-performance cost intelligence.
## Architecture

![Architecture](./assets/architecture-diagram.png)
