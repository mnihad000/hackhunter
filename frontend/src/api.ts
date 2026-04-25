import type { Goal, Prediction, Transaction } from "./demoLogic";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? (import.meta.env.DEV ? "/api" : "http://127.0.0.1:8000");

export const DEFAULT_PHONE_NUMBER = "+15555550000";

type ApiTransaction = {
  id: number;
  category: string;
  amount: number;
  occurred_at: string;
};

type ApiTransactionsResponse = {
  user_id: number;
  transactions: ApiTransaction[];
};

type ApiGoal = {
  id: number;
  name: string;
  target_amount: number;
  current_amount: number;
  remaining_amount: number;
  is_active: boolean;
};

type ApiGoalResponse = {
  user_id: number;
  goal: ApiGoal | null;
};

type ApiPrediction = {
  category: string;
  predicted_at: string;
  window_start: string;
  window_end: string;
  probability: number;
  confidence: number;
  support_count: number;
  reason_codes: string[];
};

type ApiPredictionResponse = {
  user_id: number;
  predictions: ApiPrediction[];
};

type ApiErrorResponse = {
  detail?: string;
  errors?: string[];
};

type PlaidLinkTokenResponse = {
  link_token: string;
};

type PlaidExchangeResponse = {
  user_id: number;
  plaid_item_id: string;
  institution_name: string | null;
  sync: {
    added: number;
    modified: number;
    removed: number;
  };
};

type PlaidSyncResponse = {
  user_id: number;
  sync: {
    added: number;
    modified: number;
    removed: number;
  };
};

function normalizePhoneNumber(phoneNumber: string) {
  return phoneNumber.trim();
}

function buildQuery(phoneNumber: string) {
  const params = new URLSearchParams({
    phone_number: normalizePhoneNumber(phoneNumber),
  });

  return `?${params.toString()}`;
}

function formatLabel(value: string) {
  return value
    .trim()
    .split(/[\s_-]+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
    .join(" ");
}

function formatTransactionTime(occurredAt: string) {
  const date = new Date(occurredAt);
  const now = new Date();
  const dateLabel = new Intl.DateTimeFormat("en-US", {
    hour: "numeric",
    minute: "2-digit",
  }).format(date);

  const transactionDay = new Date(date.getFullYear(), date.getMonth(), date.getDate());
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const dayDifference = Math.round((today.getTime() - transactionDay.getTime()) / 86400000);

  let prefix = new Intl.DateTimeFormat("en-US", { weekday: "long" }).format(date);
  if (dayDifference === 0) {
    prefix = "Today";
  } else if (dayDifference === 1) {
    prefix = "Yesterday";
  } else if (dayDifference > 6 || dayDifference < 0) {
    prefix = new Intl.DateTimeFormat("en-US", {
      month: "short",
      day: "numeric",
    }).format(date);
  }

  return `${prefix}, ${dateLabel}`;
}

function formatPredictionWindow(windowStart: string, windowEnd: string) {
  const start = new Date(windowStart);
  const end = new Date(windowEnd);
  const sameDay = start.toDateString() === end.toDateString();
  const timeFormat = new Intl.DateTimeFormat("en-US", {
    hour: "numeric",
    minute: "2-digit",
  });

  if (sameDay) {
    return `${timeFormat.format(start)}-${timeFormat.format(end)}`;
  }

  const dateTimeFormat = new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });

  return `${dateTimeFormat.format(start)}-${dateTimeFormat.format(end)}`;
}

function getTypicalSpend(category: string, transactions: Transaction[]) {
  const categoryKey = formatLabel(category).toLowerCase();
  const matchingTransactions = transactions.filter(
    (transaction) => transaction.category.toLowerCase() === categoryKey,
  );

  if (matchingTransactions.length === 0) {
    return 0;
  }

  const total = matchingTransactions.reduce((sum, transaction) => sum + transaction.amount, 0);
  return Number((total / matchingTransactions.length).toFixed(2));
}

async function getErrorMessage(response: Response) {
  try {
    const payload = (await response.json()) as ApiErrorResponse;
    if (typeof payload.detail === "string" && payload.detail.trim()) {
      return payload.detail;
    }

    if (Array.isArray(payload.errors) && payload.errors.length > 0) {
      return payload.errors.join(" ");
    }
  } catch {
    // Fall through to the default message when the body is not JSON.
  }

  return `${response.status} ${response.statusText}`;
}

async function request<T>(path: string, init?: RequestInit) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      Accept: "application/json",
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }

  return (await response.json()) as T;
}

function mapGoal(goal: ApiGoal | null): Goal | null {
  if (goal === null) {
    return null;
  }

  return {
    name: goal.name,
    target: goal.target_amount,
    saved: goal.current_amount,
  };
}

export async function fetchTransactions(phoneNumber: string, signal?: AbortSignal) {
  const payload = await request<ApiTransactionsResponse>(`/transactions${buildQuery(phoneNumber)}`, {
    signal,
  });

  return payload.transactions.map((transaction) => {
    const category = formatLabel(transaction.category);

    return {
      id: transaction.id,
      category,
      merchant: category,
      amount: transaction.amount,
      time: formatTransactionTime(transaction.occurred_at),
    } satisfies Transaction;
  });
}

export async function fetchGoal(phoneNumber: string, signal?: AbortSignal) {
  const payload = await request<ApiGoalResponse>(`/goals${buildQuery(phoneNumber)}`, {
    signal,
  });

  return mapGoal(payload.goal);
}

export async function saveGoal(phoneNumber: string, goal: Goal) {
  const payload = await request<ApiGoalResponse>(`/goals${buildQuery(phoneNumber)}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      name: goal.name.trim(),
      target_amount: goal.target.toFixed(2),
      current_amount: goal.saved.toFixed(2),
      is_active: true,
    }),
  });

  const mappedGoal = mapGoal(payload.goal);
  if (mappedGoal === null) {
    throw new Error("Goal save returned an empty response.");
  }

  return mappedGoal;
}

export async function fetchPrediction(
  phoneNumber: string,
  transactions: Transaction[],
  signal?: AbortSignal,
) {
  const payload = await request<ApiPredictionResponse>(`/predict${buildQuery(phoneNumber)}`, {
    signal,
  });

  const topPrediction = payload.predictions[0];
  if (!topPrediction) {
    return null;
  }

  return {
    category: formatLabel(topPrediction.category),
    window: formatPredictionWindow(topPrediction.window_start, topPrediction.window_end),
    probability: Math.round(topPrediction.probability * 100),
    amount: getTypicalSpend(topPrediction.category, transactions),
  } satisfies Prediction;
}

export async function createPlaidLinkToken(phoneNumber: string) {
  const payload = await request<PlaidLinkTokenResponse>("/plaid/link-token", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      phone_number: normalizePhoneNumber(phoneNumber),
    }),
  });

  return payload.link_token;
}

export async function exchangePlaidPublicToken(
  phoneNumber: string,
  publicToken: string,
  institution?: { institution_id?: string | null; name?: string | null },
) {
  return request<PlaidExchangeResponse>("/plaid/exchange-public-token", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      phone_number: normalizePhoneNumber(phoneNumber),
      public_token: publicToken,
      institution_id: institution?.institution_id ?? null,
      institution_name: institution?.name ?? null,
    }),
  });
}

export async function syncPlaidTransactions(phoneNumber: string) {
  return request<PlaidSyncResponse>("/plaid/sync", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      phone_number: normalizePhoneNumber(phoneNumber),
    }),
  });
}
