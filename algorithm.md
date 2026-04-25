# 🧠 Prediction Engine — PiggyBank

## 🎯 Overview

The Prediction Engine is the core intelligence of PiggyBank.

It forecasts **when a user is likely to make a purchase** and outputs:

* predicted time window
* probability of purchase
* confidence score

This enables PiggyBank to **intervene before spending happens**, not after.

---

## 🧩 Problem Formulation

We model spending as a probabilistic event:

> **P(purchase of category C at time t | user behavior history)**

Instead of predicting a single timestamp, we predict:

* likelihood of purchase within a time window
* uncertainty of that prediction

---

## 📥 Inputs

For each user and category:

* transaction timestamps
* transaction amounts
* category labels (coffee, food, etc.)

---

## 🧠 Feature Engineering

### 1. Temporal Features

* time since last purchase
* average interval between purchases
* rolling frequency (7-day, 30-day)

---

### 2. Time-of-Day Patterns

* hour distribution of purchases
* peak purchase windows

---

### 3. Behavioral Consistency

* variance of purchase intervals
* repeat streaks
* entropy of behavior

---

### 4. Recency Weighting

Recent behavior is weighted more heavily:

```python
weight = 1 / (current_time - purchase_time)
```

This allows the model to **adapt quickly to changing habits**.

---

## 🔁 Prediction Logic

### Step 1: Compute Intervals

```python
intervals = [t2 - t1, t3 - t2, ...]
```

---

### Step 2: Weighted Average Interval

```python
avg_interval = weighted_mean(intervals)
```

---

### Step 3: Estimate Next Purchase Time

```python
predicted_time = last_purchase_time + avg_interval
```

---

### Step 4: Generate Time Window

Using historical variance:

```python
window = predicted_time ± variance
```

---

### Step 5: Compute Probability

Probability is derived from:

* consistency of behavior
* frequency of purchases
* alignment with time-of-day patterns

Example:

```text
Coffee:
7:30–8:30 AM → 74% probability
```

---

## 📊 Confidence Score

Confidence is based on:

* number of historical data points
* consistency of intervals
* stability of time-of-day behavior

Example:

```text
High confidence:
- daily purchases → 80%+

Low confidence:
- irregular behavior → <50%
```

---

## ⏱️ Trigger Conditions

A nudge is triggered when:

* probability > threshold (e.g. 0.65)
* current time is within predicted window
* user has not already made the purchase

---

## 🔁 Feedback Loop

After prediction:

* Did user make the purchase?
* Did they skip?
* Did they respond to the nudge?

This updates:

* interval weighting
* confidence calibration
* behavioral profile

---

## 🧠 Design Principles

### 1. Probabilistic, not deterministic

Predictions are expressed as likelihoods, not certainties.

---

### 2. Adaptive

The system prioritizes recent behavior.

---

### 3. Explainable

Every prediction can be traced back to:

* frequency
* timing
* consistency

---

### 4. Lightweight but effective

Avoids heavy ML models while maintaining strong performance.

---

## 🚀 Future Improvements

* Gradient Boosted Models for probability estimation
* Survival analysis for time-to-event modeling
* Sequence models (LSTM / Transformer) for behavior patterns
* Personalized embeddings per user

---

## 🏆 Summary

The Prediction Engine transforms raw transaction data into:

> **actionable, time-sensitive insights**

It enables PiggyBank to act at the exact moment when behavior can still be changed.

---
