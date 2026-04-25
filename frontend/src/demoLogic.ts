export type Goal = {
  name: string;
  target: number;
  saved: number;
};

export type Transaction = {
  id: number;
  category: string;
  merchant: string;
  amount: number;
  time: string;
};

export type Prediction = {
  category: string;
  window: string;
  probability: number;
  amount: number;
};

export type CategoryTotal = {
  category: string;
  amount: number;
  percent: number;
};

export type GoalStatus = "behind" | "met" | "overfunded";

export const initialGoal: Goal = {
  name: "Bike fund",
  target: 250,
  saved: 208,
};

export const initialPrediction: Prediction = {
  category: "Coffee",
  window: "7:30-8:30 AM",
  probability: 74,
  amount: 6.5,
};

export const initialTransactions: Transaction[] = [
  { id: 1, category: "Food", merchant: "Coffee", amount: 6.5, time: "Today, 8:04 AM" },
  { id: 2, category: "Food", merchant: "Food delivery", amount: 15.2, time: "Yesterday, 7:18 PM" },
  { id: 3, category: "Transportation", merchant: "Uber", amount: 14.2, time: "Monday, 5:41 PM" },
  { id: 4, category: "Entertainment", merchant: "Movie rental", amount: 7.99, time: "Sunday, 9:12 PM" },
  { id: 5, category: "Shopping", merchant: "Phone case", amount: 11.75, time: "Saturday, 2:24 PM" },
];

export function formatCurrency(amount: number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(amount);
}

export function getGoalProgress(goal: Goal) {
  return Math.min(100, Math.round((goal.saved / goal.target) * 100));
}

export function getRemainingGoalAmount(goal: Goal) {
  return Math.max(0, goal.target - goal.saved);
}

export function getGoalStatus(goal: Goal): GoalStatus {
  if (goal.saved > goal.target) {
    return "overfunded";
  }

  if (goal.saved === goal.target) {
    return "met";
  }

  return "behind";
}

export function getCategoryTotals(transactions: Transaction[]): CategoryTotal[] {
  const total = transactions.reduce((sum, transaction) => sum + transaction.amount, 0);

  if (total === 0) {
    return [];
  }

  const totals = transactions.reduce<Record<string, number>>((accumulator, transaction) => {
    accumulator[transaction.category] =
      (accumulator[transaction.category] ?? 0) + transaction.amount;
    return accumulator;
  }, {});

  return Object.entries(totals)
    .sort(([, firstAmount], [, secondAmount]) => secondAmount - firstAmount)
    .map(([category, amount]) => ({
      category,
      amount,
      percent: Math.round((amount / total) * 100),
    }));
}
