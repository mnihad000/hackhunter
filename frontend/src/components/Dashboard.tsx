import { useMemo, useState } from "react";
import {
  initialGoal,
  initialPrediction,
  initialTransactions,
  type Goal,
} from "../demoLogic";
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

function formatCurrentDate() {
  return new Intl.DateTimeFormat("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
  }).format(new Date());
}

function Dashboard({ onBack }: DashboardProps) {
  const [goal, setGoal] = useState<Goal>(initialGoal);
  const [prediction] = useState(initialPrediction);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [nudgeTone, setNudgeTone] = useState<NudgeTone>("Gentle");
  const [nudgeFrequency, setNudgeFrequency] = useState<NudgeFrequency>("Normal");
  const currentDate = formatCurrentDate();
  const filteredTransactions = useMemo(
    () =>
      selectedCategory
        ? initialTransactions.filter((transaction) => transaction.category === selectedCategory)
        : initialTransactions,
    [selectedCategory],
  );

  return (
    <main className="dashboard-page" aria-labelledby="dashboard-title">
      <section className="dashboard-shell">
        <header className="dashboard-header">
          <div>
            <p className="dashboard-kicker">Spendly</p>
            <h1 id="dashboard-title">{currentDate}</h1>
          </div>
          <button className="secondary-action" type="button" onClick={onBack}>
            Back
          </button>
        </header>

        <PredictionCard prediction={prediction} goal={goal} />
        <GoalProgress goal={goal} onGoalChange={setGoal} />
        <WeeklyTrends transactions={initialTransactions} prediction={prediction} />
        <SpendingPieChart
          transactions={initialTransactions}
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
