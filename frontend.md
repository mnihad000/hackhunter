# Frontend Design - Spendly

## Overview

The frontend is a mobile-first Vite React demo that complements Spendly's planned SMS-based experience. It is not a replacement for SMS; it gives users a lightweight place to review predictions, goals, preferences, and recent spending.

## Current Stack

- Framework: Vite + React + TypeScript
- Styling: CSS
- Visuals: Three.js, React Three Fiber, OGL, GSAP
- Build: `npm run build` from `frontend/`

## Core Screens

### Landing

The landing screen introduces Spendly with a 3D visual scene and a direct `Get Started` call to action. The visual stack is lazy-loaded so dashboard code can remain lighter.

### Dashboard

The dashboard shows:

- next likely spend
- goal progress and editable goal values
- weekly signal cards
- category breakdown
- nudge tone and frequency settings
- SMS nudge preview
- recent transactions

## UX Principles

- Keep the first screen focused and direct.
- Make the dashboard feel actionable rather than purely informational.
- Use mobile-friendly controls and stable card dimensions.
- Tie every spending insight back to a concrete goal.

## Future Improvements

- Backend API integration for transactions and goals
- Real authentication or phone-number-based demo identity
- PWA install flow
- Accessibility pass for chart keyboard interaction
