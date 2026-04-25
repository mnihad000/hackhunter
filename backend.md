# 🔧 Backend Design — PiggyBank

## 🎯 Overview

The backend is the **core execution layer** of PiggyBank.

It is responsible for:

* receiving SMS messages
* processing transactions
* running predictions
* triggering nudges
* integrating with the AI agent (Gemini)

Built using **FastAPI**, the backend acts as the system’s brain.

---

## 🏗️ Tech Stack

* Framework: FastAPI (Python)
* Database: PostgreSQL
* Messaging: Twilio
* AI Layer: Gemini API
* Scheduler: Background worker (cron / async loop)

---

## 📂 Project Structure

```text id="nj9yok"
backend/
│
├── main.py                # FastAPI entry point
├── routes/
│   ├── sms.py            # Twilio webhook
│   ├── predict.py        # prediction endpoints
│   └── chat.py           # agent interaction
│
├── services/
│   ├── transaction.py    # parsing + saving
│   ├── prediction.py     # prediction engine
│   ├── agent.py          # Gemini decision + messaging
│   └── scheduler.py      # background jobs
│
├── models/
│   ├── user.py
│   ├── transaction.py
│   └── goal.py
│
└── db/
    └── database.py
```

---

## 📥 1. SMS Webhook (Core Entry Point)

### Endpoint

```http id="dy4r98"
POST /sms
```

### Input (from Twilio)

```json id="6d0zpx"
{
  "From": "+1234567890",
  "Body": "coffee 6.50"
}
```

---

### Responsibilities

* identify user (phone number = user ID)
* parse message
* route logic:

  * transaction
  * response
  * command

---

### Example Implementation

```python id="fl3p7c"
@app.post("/sms")
async def receive_sms(request: Request):
    data = await request.form()
    user = data.get("From")
    message = data.get("Body")

    if is_transaction(message):
        save_transaction(user, message)
        return send_sms(user, "Logged!")

    elif is_reply(message):
        process_feedback(user, message)
        return send_sms(user, "Got it 👍")
```

---

## 🧾 2. Transaction Service

### Responsibilities

* parse user input
* extract:

  * category
  * amount
* store in database

---

### Example

```python id="7qhz3v"
def parse_transaction(message):
    # "coffee 6.50"
    parts = message.split()
    return {
        "category": parts[0],
        "amount": float(parts[1])
    }
```

---

## 🧠 3. Prediction Service

### Responsibilities

* fetch user transaction history
* compute patterns
* output prediction

---

### Core Output

```json id="t8j4bb"
{
  "category": "coffee",
  "probability": 0.72,
  "time_window": "7:30–8:30",
  "confidence": 0.8
}
```

---

### Core Functions

```python id="4v8xmq"
def compute_intervals(transactions):
    return [t2 - t1 for t1, t2 in pairs]

def predict_next(transactions):
    interval = weighted_avg(compute_intervals(transactions))
    return last_time + interval
```

---

## 🤖 4. Agent Service (Gemini Integration)

### Responsibilities

* decide whether to send nudge
* generate message

---

### Input

```json id="e0dfsv"
{
  "prediction": {...},
  "user_context": {...}
}
```

---

### Output

```json id="j7yoqf"
{
  "send": true,
  "message": "Skip coffee today — closer to your goal"
}
```

---

### Implementation Sketch

```python id="1kj0cq"
def generate_message(prediction, context):
    prompt = build_prompt(prediction, context)
    return call_gemini(prompt)
```

---

## 📤 5. SMS Sender

### Using Twilio API

```python id="g3e0l5"
from twilio.rest import Client

client = Client(SID, TOKEN)

def send_sms(to, body):
    client.messages.create(
        body=body,
        from_="+YOUR_NUMBER",
        to=to
    )
```

---

## ⏱️ 6. Scheduler (Critical for Nudges)

### Responsibilities

* run every X minutes
* check predictions
* trigger nudges

---

### Example Loop

```python id="fxn0yf"
while True:
    for user in users:
        prediction = get_prediction(user)

        if should_nudge(prediction):
            message = agent_decide(prediction)
            send_sms(user, message)

    sleep(60)
```

---

## 🗄️ 7. Database Schema (Simplified)

### Users

```text id="4o2c7v"
id (phone number)
goal
preferences
```

---

### Transactions

```text id="eqd8rn"
id
user_id
category
amount
timestamp
```

---

### Feedback

```text id="smclrb"
id
user_id
response
timestamp
```

---

## 🔁 8. Feedback Processing

### Responsibilities

* interpret replies
* update behavior model

---

### Example

```python id="t3z9f1"
def process_feedback(user, message):
    if "skip" in message:
        increase_confidence(user)
```

---

## ⚠️ Error Handling

* invalid input → ask user to reformat
* failed SMS → retry
* missing data → fallback logic

---

## 🧠 Design Principles

### 1. Stateless endpoints

All state lives in DB.

---

### 2. Modular services

Each component is independent.

---

### 3. Fast responses

Webhook must respond quickly.

---

### 4. Async processing

Heavy tasks run in background.

---

## 🚀 Future Improvements

* queue system (Celery / Redis)
* better NLP parsing
* ML model integration
* scalable microservices

---

## 🏆 Summary

The backend orchestrates:

> **input → prediction → decision → action**

It is the operational core that enables PiggyBank to function as a real-time AI system.

---
