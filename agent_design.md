# 🤖 Agent Design — PiggyBank

## 🎯 Overview

The Agent Layer transforms raw predictions into **intelligent, human-like financial guidance**.

While the Prediction Engine determines *when a user is likely to spend*, the Agent decides:

* **Should we intervene?**
* **When should we intervene?**
* **How should we communicate?**

This layer is powered by **Gemini** and acts as PiggyBank’s “brain for decision-making and communication.”

---

## 🧠 Core Responsibility

Convert structured predictions into **context-aware actions and messages**.

### Input (from Prediction Engine):

```json
{
  "category": "coffee",
  "probability": 0.74,
  "time_window": "7:30–8:30 AM",
  "confidence": 0.81
}
```

### Input (from User Context):

```json
{
  "goal": "save $250 for a bike",
  "recent_behavior": "skipped last 2 days",
  "response_pattern": "ignores frequent nudges"
}
```

### Output:

* decision (send nudge or not)
* timing (now, later, skip)
* message (personalized SMS)

---

## ⚖️ Decision Layer

### Problem Formulation

> Should we send a nudge at time t to maximize positive behavior change?

---

### Basic Logic (baseline)

```python
if probability > 0.65 and within_time_window:
    send_nudge()
```

---

### AI-Enhanced Decision (Gemini)

Instead of static rules, we use Gemini to evaluate:

* probability of purchase
* user responsiveness
* goal relevance
* recent behavior

---

### Example Decision Reasoning

**Input:**

```json
{
  "probability": 0.72,
  "recent_behavior": "ignored last 3 nudges",
  "goal_progress": "low"
}
```

**Gemini Output:**

```json
{
  "decision": "delay",
  "reason": "user likely fatigued by frequent nudges"
}
```

---

## 💬 Messaging Layer

The Agent generates messages that are:

* personalized
* context-aware
* goal-oriented
* emotionally intelligent

---

### Message Types

#### 1. Preventive Nudge

> “You’re likely to grab coffee soon 👀
> Skipping today gets you $6 closer to your bike.”

---

#### 2. Reinforcement

> “Nice — you skipped coffee yesterday 🔥
> Keep it up.”

---

#### 3. Reflective Insight

> “You tend to spend more on Fridays. Want to set a limit?”

---

#### 4. Light Humor / Personality

> “You said ‘just one coffee’ yesterday too 😭”

---

## 🧠 Prompt Design (Gemini)

### System Prompt (simplified)

```text
You are Piggy, a friendly financial assistant.

Your goals:
- Help users reduce unnecessary spending
- Be encouraging, not judgmental
- Connect actions to user goals
- Keep messages short and conversational
```

---

### Example Prompt

```text
User behavior:
- Likely to buy coffee in 30 minutes (74% probability)
- Skipped last 2 days
- Saving for a $250 bike

Generate a short SMS message encouraging smarter choice.
```

---

## 🔁 Feedback Loop

The Agent continuously improves based on:

* user replies
* whether the user followed the suggestion
* engagement patterns

---

### Updates:

* adjust tone (more direct vs softer)
* adjust frequency (reduce spam)
* refine timing

---

## ⚠️ Constraints

To maintain system reliability:

* Gemini **does NOT override prediction probability**
* Gemini **does NOT generate numerical predictions**
* Gemini only:

  * decides actions
  * generates messaging

---

## 🧩 Integration with System

```text
Prediction Engine → Agent Decision → Message Generation → SMS (Twilio) → User
                                                ↑
                                         Feedback Loop
```

---

## 🏆 Design Principles

### 1. Human-first

Messages should feel like texting a friend.

---

### 2. Non-judgmental

Avoid guilt-based messaging.

---

### 3. Actionable

Every message should suggest a clear alternative or insight.

---

### 4. Adaptive

Agent evolves with user behavior.

---

## 🚀 Future Improvements

* Reinforcement learning for optimal nudging
* Personalized tone modeling
* Multi-step conversations
* Emotional state detection

---

## 🧠 Summary

The Agent Layer turns PiggyBank from:

> a prediction system

into:

> a real-time behavioral AI companion

It is the bridge between **data** and **human decision-making**.

---
