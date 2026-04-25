# 🏗️ System Architecture — PiggyBank

## 🎯 Overview

PiggyBank is a **real-time, event-driven system** that processes user transactions, predicts future spending, and delivers proactive nudges via SMS.

The architecture is designed to be:

* **modular** (clear separation of components)
* **scalable** (can handle more users/features)
* **low-latency** (real-time interaction via SMS)

---

## 🧩 High-Level Architecture

```text id="7l3n2p"
User (SMS)
   ↓
Twilio Webhook
   ↓
Backend API (FastAPI)
   ↓
┌───────────────────────────────┐
│ Core Services                 │
│                               │
│ • Transaction Processor       │
│ • Prediction Engine           │
│ • Agent (Gemini)              │
└───────────────────────────────┘
   ↓
Database (PostgreSQL)
   ↓
Scheduler / Background Jobs
   ↓
Twilio SMS Response
   ↓
User
```

---

## 📱 Core Components

---

### 1. User Interface Layer

#### Primary Interface:

* SMS via Twilio

#### Secondary Interface:

* Mobile-first web dashboard using Next.js

---

### 2. Backend API (FastAPI)

The central system that handles:

* incoming SMS messages
* transaction processing
* prediction requests
* agent decisions
* outgoing SMS responses

---

### 3. Transaction Processor

Responsible for:

* parsing user messages
* extracting structured data:

  * category
  * amount
* storing transactions in database

---

### 4. Prediction Engine

Core logic that:

* analyzes transaction history
* computes behavioral patterns
* predicts future spending

Outputs:

* probability of purchase
* predicted time window
* confidence score

---

### 5. Agent Layer (Gemini)

Responsible for:

* deciding whether to send a nudge
* determining timing
* generating personalized messages

---

### 6. Database (PostgreSQL)

Stores:

* user profiles (phone number as ID)
* transaction history
* prediction metadata
* user goals
* feedback signals

---

### 7. Scheduler / Background Jobs

Runs continuously to:

* check predictions
* trigger nudges at the right time

---

## 🔁 Data Flow

### 1. Transaction Ingestion

```text id="6cvq5t"
User → SMS → Twilio → Backend → Database
```

---

### 2. Prediction Pipeline

```text id="8mghm3"
Database → Prediction Engine → Predicted Events
```

---

### 3. Decision + Messaging

```text id="7u6w0z"
Prediction → Agent (Gemini) → Message → Twilio → User
```

---

### 4. Feedback Loop

```text id="qln8xl"
User Response → Backend → Database → Model Updates
```

---

## ⏱️ Real-Time vs Async Processing

### Real-Time (synchronous)

* receiving SMS
* sending immediate responses

---

### Asynchronous

* prediction checks
* scheduled nudges
* background model updates

---

## 🔌 External Services

* Messaging: Twilio
* AI Layer: Gemini API
* (Optional) OCR: Google Vision API

---

## ⚙️ Deployment Architecture

```text id="3zzh0o"
Frontend (Next.js) → Vercel
Backend (FastAPI) → Cloud VM / Docker
Database → Managed PostgreSQL
Twilio → SMS Gateway
```

---

## 🧠 Design Principles

### 1. Separation of Concerns

Each component has a single responsibility.

---

### 2. Event-Driven Flow

System reacts to:

* user messages
* predicted events

---

### 3. Scalability

Can extend to:

* more users
* more categories
* more complex models

---

### 4. Low Friction

SMS-first design ensures:

* no app installs
* instant usability

---

## 🚀 Future Architecture Improvements

* Message queue (Kafka / Redis)
* Feature store for ML
* Real-time streaming pipeline
* Microservices split

---

## 🏆 Summary

PiggyBank’s architecture enables:

> **real-time prediction → intelligent decision → instant user feedback**

This allows the system to intervene at the exact moment when behavior can still be changed.

---

