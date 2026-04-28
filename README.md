# Azure Cost Governance Platform

![Azure](https://img.shields.io/badge/Azure-Cost_Governance-0078D4?logo=microsoft-azure&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![Status](https://img.shields.io/badge/Status-Complete-brightgreen)

## 🌐 Live Dashboard
**[https://stcostdashboard6431.z13.web.core.windows.net](https://stcostdashboard6431.z13.web.core.windows.net)**

---

## Problem
Companies migrate to Azure expecting cost savings but receive unexpected bills with no visibility, no automation, and no accountability over who is spending what.

## Solution
A serverless Azure cost intelligence platform that:
- Pulls real cost data daily from the Cost Management API
- Detects spending anomalies using a 7-day rolling average algorithm
- Automatically sends formatted alerts via Logic Apps when anomalies are detected
- Enforces cost ownership through Azure Policy tagging across all resources
- Displays everything on a live dashboard with sub-second performance

---

## Architecture

```
Azure Cost Management API
        │ (daily scheduled pull)
        ▼
Azure Functions (Python 3.11)
├── CostDataFetcher  → runs 6:00 AM daily
└── AnomalyDetector  → runs 6:30 AM daily
        │
        ├──────────────────────────────────┐
        ▼                                  ▼
Azure Blob Storage                  Log Analytics (KQL)
(cache layer)                       (query + analysis)
latest-costs.json                          │
latest-anomaly.json                        │
        │                                  │
        ▼                                  ▼
Static Web Dashboard            Azure Monitor (alerts)
(live cost intelligence)                   │
                                           ▼
                                   Azure Logic Apps
                                   (auto-remediation)
                                   ├── Email alerts
                                   └── Anomaly notifications

Azure Policy → enforces Owner / Environment / CostCenter tags
Managed Identity → zero credential storage across all services
```

---

## Tech Stack

| Service | Purpose |
|---|---|
| Azure Cost Management API | Cost data source |
| Azure Functions (Python 3.11) | Backend logic + data processing |
| Azure Blob Storage | Caching layer (latest-costs.json) |
| Log Analytics Workspace | KQL queries + trend analysis |
| Azure Monitor | Alert engine + thresholds |
| Azure Logic Apps | Email automation + remediation |
| Azure Static Web App | Live cost dashboard |
| Azure Policy | Tag enforcement across resources |
| Managed Identity | Zero credential storage |

---

## Key Features

**Anomaly Detection** — Compares today's spend against a 7-day rolling average. Triggers an alert when spending exceeds 20% above normal.

**Auto-Remediation** — When an anomaly is detected, Logic Apps automatically sends a formatted email alert with cost details, spike percentage, and a direct link to the dashboard.

**Cost Ownership** — Azure Policy enforces required tags (Owner, Environment, CostCenter) on all resources, enabling cost attribution by team and environment.

**Live Dashboard** — Fetches real cost data from Blob Storage every 5 minutes showing MTD spend, budget forecast, top services by cost, and active anomalies.

**Security** — All services authenticate via Managed Identity. Zero credentials stored in code or configuration.

---

## Data Flow

```
1. CostDataFetcher pulls data from Cost Management API
2. Data cached in Blob Storage as latest-costs.json
3. AnomalyDetector reads cache → compares vs 7-day average
4. If spike > 20% → saves ANOMALY to latest-anomaly.json
5. Logic App triggered → formatted email sent automatically
6. Dashboard reads Blob Storage → displays live data
```

---

## Project Structure

```
azure-cost-governance-platform/
├── dashboard/
│   └── index.html          → live cost intelligence dashboard
├── functions/
│   ├── function_app.py     → CostDataFetcher + AnomalyDetector + TestAnomaly
│   ├── host.json
│   └── requirements.txt
├── infra/                  → IaC (future Bicep/Terraform)
├── logicapps/              → Logic App workflow exports
└── README.md
```

---

## Azure Resources

| Resource | Type | Purpose |
|---|---|---|
| rg-cost-governance | Resource Group | All project resources |
| func-cost-governance | Function App | Python backend |
| logic-cost-alert | Logic App | Email automation |
| stcostdashboard6431 | Storage Account | Dashboard + cost data cache |
| law-cost-governance | Log Analytics | KQL queries + monitoring |
| budget-cost-governance | Budget | Alerts at 50/80/100% |

---

## Interview Q&A

**Q: Why not just use Azure Cost Management natively?**
Native tools are slower, harder to automate, and not optimized for custom anomaly detection or executive reporting. This system adds performance via caching, automation via Logic Apps, and extensibility via Python functions.

**Q: What happens when the API is throttled?**
The system uses Blob Storage as a cache layer. If the API is unavailable, the dashboard still serves the last cached data. The timestamp shows when data was last refreshed so users know the data age.

**Q: How do you ensure data accuracy?**
The Cost Management API has a 24-48 hour delay. The dashboard shows a "last refreshed" timestamp and I explicitly avoid claiming real-time accuracy — I call it near real-time and explain the offset clearly.

---

## Resume Bullets

```
- Built a serverless Azure cost governance platform with automated anomaly 
  detection, reducing unexpected cost spikes via Logic Apps auto-remediation.

- Implemented daily cost data pipeline using Azure Functions (Python) and 
  Blob Storage caching, achieving near real-time dashboard performance.

- Enforced cost ownership using Azure Policy tagging (Owner, Environment, 
  CostCenter) and Managed Identity for zero-credential authentication.
```

---

## Progress

- [x] Phase 1 — Foundation, Budget Alerts, Logic Apps, Dashboard
- [x] Phase 2 — Azure Functions, Real Cost Data, Log Analytics, KQL
- [x] Phase 3 — Anomaly Detection + Auto-Remediation
- [x] Phase 4 — Live Data Dashboard, End-to-End Pipeline
- [x] Phase 5 — Portfolio Polish, README, Architecture
