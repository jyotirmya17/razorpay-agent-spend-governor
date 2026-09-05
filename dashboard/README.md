# Agent Spend Governor — Evaluator Dashboard

**Next.js 16 Control Plane & Risk Visualization Interface for the Agent Spend Governor.**

> **Note**: The dashboard is a thin evaluator/control-plane client over the FastAPI backend; governance decisions remain authoritative in the backend.

---

## Overview

The **Evaluator Dashboard** is a developer-facing web application that provides real-time visibility into the Agent Spend Governor backend. It allows evaluators and security engineers to inspect live agent spend metrics, policy mandates, behavioral risk scores, cryptographic audit timelines, and run interactive failure injection scenarios.

---

## Tech Stack & System Requirements

- **Framework**: Next.js 16.3.4 (App Router, Turbopack)
- **Runtime**: Node.js 20.9.0+ & npm
- **Language**: TypeScript (Strict Mode)
- **Styling**: Tailwind CSS, Modern Dark Mode UI
- **Icons**: Lucide React
- **Backend API**: FastAPI (`http://localhost:8000`)

---

## Getting Started

### 1. Prerequisites
Ensure the FastAPI backend is running:
```powershell
# In the repository root
python -m uvicorn gateway.main:app --port 8000
```

### 2. Start Development Server
```powershell
cd dashboard
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## Application Structure & Routes

| Route | Page Name | Description |
| :--- | :--- | :--- |
| `/` | **Overview Dashboard** | Real-time transaction volume, risk breakdown, decision stats, and recent activity feed. |
| `/transactions` | **Transactions Explorer** | Search, filter, and inspect transaction lifecycle states (`SUCCEEDED`, `BLOCKED`, `FLAGGED`, `UNKNOWN`). |
| `/agents` | **Agent Management** | View registered AI agents, spending baselines, active mandates, and transaction history. |
| `/mandates` | **Policy Mandates** | Inspect active mandates, transaction caps, daily/weekly cumulative usage, and live revocation controls. |
| `/risk` | **Risk & Provenance** | Deep-dive into IsolationForest anomaly scores, feature contributions, and provenance trust evaluation. |
| `/audit` | **Audit Timeline** | Cryptographic SHA-256 tamper-evident hash chain viewer with instant verification tooling. |
| `/demo` | **Demo Control Plane** | **Interactive Evaluator Hub**: Trigger 6 pre-configured failure injection & governance scenarios. |

---

## Production Build

To verify the TypeScript compilation and generate static production bundles:

```powershell
npm run build
```

**Verified Build Output**:
- **0 TypeScript Errors**
- **10 Static Pages Generated**
