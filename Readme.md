# 🐷 PiggyBank — Make Your Money Talk

## 🚀 Overview

PiggyBank is a **real-time financial behavior agent** that helps users make smarter spending decisions *before* they happen.

Instead of tracking what you already spent, PiggyBank predicts what you’re about to spend — and nudges you at the exact moment it matters.

> Not “you spent too much”
> 👉 but “you’re about to spend — here’s a better choice”

---

## 💡 The Problem

Most financial stress doesn’t come from big purchases.

It comes from:

* $6 coffees
* $15 food deliveries
* small, repeated habits

These “invisible expenses”:

* quietly drain your money
* reduce financial confidence
* go unnoticed in the moment

---

## 🎯 The Solution

PiggyBank is a **messaging-first AI system** that:

1. Learns your spending habits
2. Predicts upcoming purchases
3. Nudges you *before* you spend
4. Connects daily decisions to long-term goals

---

## 📱 Core Experience (SMS-Based)

PiggyBank works like texting a smart friend.

### Example Flow:

**User texts Piggy:**

```
coffee 6.50
```

**Piggy responds:**

```
Oink 🐷 Got it — logged your coffee!
```

---

### Later (prediction kicks in):

**Piggy sends:**

```
You're likely to grab coffee soon 👀  
Skip today → you're $6 closer to your $250 bike
```

**User replies:**

```
maybe 😭
```

**Piggy adapts and responds intelligently.**

---

## 🧠 How It Works

### 1. Transaction Ingestion

* SMS input (primary)
* Optional receipt image (OCR)

Users can:

* type purchases manually
* send receipt photos for automatic extraction

---

### 2. Prediction Engine (Core System)

PiggyBank models spending behavior using:

* time between purchases
* time-of-day patterns
* frequency & consistency
* recency-weighted behavior

It outputs:

* predicted purchase window
* probability of purchase
* confidence score

---

### 3. AI Decision Layer

Using **Gemini**, Piggy decides:

* whether to send a nudge
* when to send it
* how strong the message should be

---

### 4. Conversational Agent

Piggy communicates via SMS:

* proactive nudges
* goal-based motivation
* behavioral feedback
* financial insights

---

## 🏗️ Architecture

```
User (SMS) 
   ↓
Twilio Webhook
   ↓
Backend (FastAPI)
   ↓
Prediction Engine
   ↓
Gemini Decision Layer
   ↓
Twilio Response (SMS)
   ↓
User
   ↓
Feedback Loop → Model Updates
```

---

## 🛠️ Tech Stack

* **Messaging:** Twilio (SMS)
* **Frontend (Dashboard):** Next.js (mobile-first web)
* **Backend:** FastAPI (Python)
* **Database:** PostgreSQL
* **AI Layer:** Gemini API
* **Optional:** OCR for receipt processing

---

## 📱 Design Philosophy

PiggyBank is built **mobile-first**, but not as a traditional app.

👉 Primary interface: **SMS (real-time, zero friction)**
👉 Secondary interface: **lightweight web dashboard**

This makes the experience:

* immediate
* natural
* integrated into real life

---

## 🔥 Key Features

* 📊 Predictive spending detection
* 💬 Real-time SMS nudges
* 🧠 Adaptive behavior learning
* 🎯 Goal-based motivation
* 🧾 Receipt parsing (optional)
* 🤖 Conversational financial assistant

---

## 🏆 What Makes PiggyBank Different

Most finance apps are **reactive**:

> “Here’s what you spent”

PiggyBank is **proactive**:

> “Here’s what you’re about to spend — and what to do instead”

---

## 🔁 Feedback Loop

Piggy continuously learns from user behavior:

* Did the user follow the nudge?
* Did they ignore it?
* Did they respond?

This updates:

* prediction accuracy
* messaging tone
* intervention timing

---

## 📈 Future Improvements

* Bank integration via Plaid
* Advanced ML prediction models
* Reinforcement learning for nudging
* Personalized financial insights dashboard

---

## 👥 Team

Built by a 2-person team focused on:

* behavioral AI
* real-time systems
* human-centered design

---

## ⚡ Vision

PiggyBank isn’t just a budgeting tool.

It’s a **real-time behavioral feedback system** that turns small daily decisions into meaningful financial progress.

---
