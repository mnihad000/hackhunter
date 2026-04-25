import { useEffect, useMemo, useState } from "react";
import {
  DEFAULT_PHONE_NUMBER,
  fetchGoal,
  fetchPrediction,
  fetchTransactions,
  saveGoal,
} from "../api";
import type { Goal, Prediction, Transaction } from "../demoLogic";
import GoalProgress from "./GoalProgress";
import NudgeSettings, { type NudgeFrequency, type NudgeTone } from "./NudgeSettings";
import PlaidConnect from "./PlaidConnect";
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
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [goal, setGoal] = useState<Goal | null>(null);
  const [prediction, setPrediction] = useState<Prediction | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [nudgeTone, setNudgeTone] = useState<NudgeTone>("Gentle");
  const [nudgeFrequency, setNudgeFrequency] = useState<NudgeFrequency>("Normal");
  const activePhoneNumber = DEFAULT_PHONE_NUMBER;
  const [refreshKey, setRefreshKey] = useState(0);
  const [isSavingGoal, setIsSavingGoal] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [goalError, setGoalError] = useState<string | null>(null);
  const currentDate = formatCurrentDate();

  useEffect(() => {
    const abortController = new AbortController();

    async function loadDashboardData() {
      setLoadError(null);
      setGoalError(null);

      try {
        const transactionsPromise = fetchTransactions(activePhoneNumber, abortController.signal);
        const goalPromise = fetchGoal(activePhoneNumber, abortController.signal);
        const nextTransactions = await transactionsPromise;
        const [nextGoal, nextPrediction] = await Promise.all([
          goalPromise,
          fetchPrediction(activePhoneNumber, nextTransactions, abortController.signal),
        ]);

        if (abortController.signal.aborted) {
          return;
        }

        setTransactions(nextTransactions);
        setGoal(nextGoal);
        setPrediction(nextPrediction);
      } catch (error) {
        if (abortController.signal.aborted) {
          return;
        }

        const message =
          error instanceof Error ? error.message : "Unable to load dashboard data right now.";
        setLoadError(message);
        setTransactions([]);
        setGoal(null);
        setPrediction(null);
      }
    }

    void loadDashboardData();

    return () => abortController.abort();
  }, [activePhoneNumber, refreshKey]);

  useEffect(() => {
    if (
      selectedCategory !== null &&
      !transactions.some((transaction) => transaction.category === selectedCategory)
    ) {
      setSelectedCategory(null);
    }
  }, [selectedCategory, transactions]);

  const filteredTransactions = useMemo(
    () =>
      selectedCategory
        ? transactions.filter((transaction) => transaction.category === selectedCategory)
        : transactions,
    [selectedCategory, transactions],
  );

  async function handleGoalSave(nextGoal: Goal) {
    setIsSavingGoal(true);
    setGoalError(null);

    try {
      const savedGoal = await saveGoal(activePhoneNumber, nextGoal);
      setGoal(savedGoal);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Unable to save your goal right now.";
      setGoalError(message);
    } finally {
      setIsSavingGoal(false);
    }
  }

  function handleRefreshClick() {
    setRefreshKey((currentKey) => currentKey + 1);
  }

  return (
    <main className="dashboard-page" aria-labelledby="dashboard-title">
      <section className="dashboard-shell">
        <header className="dashboard-header">
          <div>
            <p className="dashboard-kicker">Spendly</p>
            <h1 id="dashboard-title">{currentDate}</h1>
          </div>
          <div className="header-actions">
            <button className="secondary-action" type="button" onClick={onBack}>
              Back
            </button>
          </div>
        </header>

        {loadError && <p className="status-banner error dashboard-alert">{loadError}</p>}

        <PlaidConnect phoneNumber={activePhoneNumber} onSynced={handleRefreshClick} />
        <PredictionCard prediction={prediction} goal={goal} />
        <GoalProgress
          goal={goal}
          isSaving={isSavingGoal}
          saveError={goalError}
          onGoalSave={handleGoalSave}
        />
        <WeeklyTrends transactions={transactions} prediction={prediction} />
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
