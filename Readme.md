# Spendly - Predictive Spending Demo

## Overview

Spendly is a frontend demo for an SMS-first financial guidance product. It shows how a real-time assistant could predict everyday spending habits and connect those habits to a savings goal.

The current repository is intentionally frontend-only. Backend, Twilio, database, and AI agent details are captured in the design docs as future implementation notes.

## Current App

- Vite + React dashboard
- 3D landing experience loaded only on the landing screen
- Mock prediction, transaction, goal, and nudge preference data
- Interactive goal editing and category filtering
- SMS nudge preview without a live SMS/chat integration

## Demo Flow

1. Open the landing page.
2. Click `Get Started`.
3. Edit the savings goal, filter category spending, and review the nudge preview.

## Tech Stack

- Frontend: Vite, React, TypeScript
- Styling: CSS with responsive grid/flex layouts
- Visuals: Three.js, React Three Fiber, OGL, GSAP
- Planned backend: FastAPI, PostgreSQL, Twilio, Gemini

## Local Development

```bash
cd frontend
npm install
npm run dev
```

## Build

```bash
cd frontend
npm run build
```

## Known Technical Notes

- The production build currently surfaces a dependency warning from `three-mesh-bvh@0.7.8`, which is pulled through `@react-three/drei`. The package is deprecated for Three.js compatibility. The safest follow-up is to refresh the Three/R3F/Drei dependency set together and regenerate `frontend/package-lock.json`.
- The 3D landing scene is code-split from the dashboard so the dashboard path avoids loading the visual stack up front.

## Future Improvements

- FastAPI mock or real API for transactions, goals, and predictions
- Twilio webhook and outbound SMS integration
- Persistence for user preferences and goal progress
- PWA support and accessibility audit
