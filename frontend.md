# 📱 Frontend Design — PiggyBank

## 🎯 Overview

The frontend is a **mobile-first, lightweight interface** that complements PiggyBank’s SMS-based experience.

PiggyBank is **not a traditional app** — the primary interaction happens through SMS.
The frontend exists to:

* visualize spending
* show predictions
* track goals
* provide a clean, minimal dashboard

---

## 🧠 Design Philosophy

### 1. Mobile-First

The UI is designed for phone screens first:

* narrow layouts
* large touch targets
* minimal navigation

---

### 2. Chat > Dashboard

PiggyBank is fundamentally:

> a conversation, not a spreadsheet

The frontend supports the experience, it doesn’t replace it.

---

### 3. Low Friction

* no complex onboarding
* simple views
* fast load times

---

## 🛠️ Tech Stack

* Framework: Next.js
* Styling: Tailwind CSS (recommended)
* Deployment: Vercel

---

## 📂 Project Structure

```text
frontend/
│
├── pages/
│   ├── index.tsx        # dashboard
│   ├── chat.tsx         # optional web chat
│   └── goals.tsx        # savings goals
│
├── components/
│   ├── TransactionList.tsx
│   ├── PredictionCard.tsx
│   ├── GoalProgress.tsx
│   └── ChatBubble.tsx
│
├── styles/
└── utils/api.ts
```

---

## 📱 Core Screens

---

## 1. Dashboard (Main Screen)

### Purpose:

Quick overview of user finances

### Displays:

* recent transactions
* predicted upcoming spend
* goal progress

---

### Example Layout

```text
--------------------------------
🐷 PiggyBank

Next likely spend:
☕ Coffee in ~30 min (74%)

You’re $42 away from your bike 🚲

Recent:
- Coffee $6.50
- Uber $14.20
--------------------------------
```

---

## 2. Prediction Card

### Purpose:

Highlight upcoming behavior

### Displays:

* category
* time window
* probability

---

### Example

```text
☕ Coffee
Likely at 7:30–8:30 AM
Probability: 74%
```

---

## 3. Goal Tracker

### Purpose:

Make spending meaningful

---

### Displays:

* goal (e.g. bike)
* progress bar
* remaining amount

---

### Example

```text
🚲 Bike Goal: $250

██████████░░░░░░ 40%

$150 remaining
```

---

## 4. Chat View (Optional)

### Purpose:

Mirror SMS interaction in browser

---

### Features:

* message bubbles
* system replies
* user input

---

### Example

```text
Piggy: You’re likely to grab coffee soon 👀
User: yeah probably
Piggy: Skip today → closer to your goal
```

---

## 🔌 API Integration

Frontend communicates with backend via REST endpoints.

---

### Example Calls

```javascript
// fetch transactions
GET /transactions

// fetch predictions
GET /predict

// fetch goals
GET /goals
```

---

## 📱 Mobile Optimization

### Techniques:

* responsive layouts
* flex/grid
* viewport scaling

---

### Tailwind Example

```html
<div class="max-w-md mx-auto p-4">
```

👉 Keeps UI narrow like a phone screen

---

## ⚡ Performance Considerations

* minimal state
* lightweight components
* lazy loading if needed

---

## 🧠 UX Principles

### 1. Clarity over complexity

Avoid overwhelming users with data

---

### 2. Actionable insights

Every screen should answer:

> “What should I do?”

---

### 3. Emotional connection

Tie spending to goals

---

### 4. Consistency with SMS

Frontend messaging should match Piggy’s tone

---

## 🚀 Future Improvements

* PWA support (add to home screen)
* push notifications
* richer analytics
* animations / micro-interactions

---

## 🏆 Summary

The frontend is:

> **a simple, mobile-first interface that reinforces PiggyBank’s SMS-driven experience**

It provides visibility, but the real magic happens in the conversation.

---
