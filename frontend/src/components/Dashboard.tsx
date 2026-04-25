import { useMemo, useState } from "react";
import GoalProgress from "./GoalProgress";
import NudgeSettings, { type NudgeFrequency, type NudgeTone } from "./NudgeSettings";
import PredictionCard from "./PredictionCard";
import SmsPreview from "./SmsPreview";
import SpendingPieChart from "./SpendingPieChart";
import TransactionList from "./TransactionList";
import WeeklyTrends from "./WeeklyTrends";

type DashboardProps = {
  onBack: () => void;
};

export type Goal = {
  name: string;
  target: number;
  saved: number;
};

const prediction = {
  category: "Coffee",
  window: "7:30-8:30 AM",
  probability: 74,
  amount: 6.5,
};

const initialGoal: Goal = {
  name: "Bike fund",
  target: 250,
  saved: 208,
};

const transactions = [
  { id: 1, category: "Food", merchant: "Coffee", amount: 6.5, time: "Today, 8:04 AM" },
  { id: 2, category: "Food", merchant: "Food delivery", amount: 15.2, time: "Yesterday, 7:18 PM" },
  { id: 3, category: "Transportation", merchant: "Uber", amount: 14.2, time: "Monday, 5:41 PM" },
  { id: 4, category: "Entertainment", merchant: "Movie rental", amount: 7.99, time: "Sunday, 9:12 PM" },
  { id: 5, category: "Shopping", merchant: "Phone case", amount: 11.75, time: "Saturday, 2:24 PM" },
];

function Dashboard({ onBack }: DashboardProps) {
  const [goal, setGoal] = useState<Goal>(initialGoal);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [nudgeTone, setNudgeTone] = useState<NudgeTone>("Gentle");
  const [nudgeFrequency, setNudgeFrequency] = useState<NudgeFrequency>("Normal");

  const filteredTransactions = useMemo(
    () =>
      selectedCategory
        ? transactions.filter((transaction) => transaction.category === selectedCategory)
        : transactions,
    [selectedCategory],
  );

  return (
    <main className="dashboard-page" aria-labelledby="dashboard-title">
      <section className="dashboard-shell">
        <header className="dashboard-header">
          <div>
            <p className="dashboard-kicker">PiggyBank</p>
            <h1 id="dashboard-title">Today</h1>
          </div>
          <button className="secondary-action" type="button" onClick={onBack}>
            Landing
          </button>
        </header>

        <PredictionCard prediction={prediction} goal={goal} />
        <GoalProgress goal={goal} onGoalChange={setGoal} />
        <WeeklyTrends />
        <SpendingPieChart
          transactions={transactions}
          selectedCategory={selectedCategory}
          onSelectCategory={setSelectedCategory}
        />
        <NudgeSettings
          tone={nudgeTone}
          frequency={nudgeFrequency}
          onToneChange={setNudgeTone}
          onFrequencyChange={setNudgeFrequency}
        />
        <SmsPreview
          prediction={prediction}
          goal={goal}
          tone={nudgeTone}
          frequency={nudgeFrequency}
        />
        <TransactionList
          transactions={filteredTransactions}
          selectedCategory={selectedCategory}
          onClearCategory={() => setSelectedCategory(null)}
        />
      </section>
    </main>
  );
}

export default Dashboard;
