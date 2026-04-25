import { type FormEvent, useEffect, useMemo, useState } from "react";
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
  const [phoneNumberDraft, setPhoneNumberDraft] = useState(DEFAULT_PHONE_NUMBER);
  const [activePhoneNumber, setActivePhoneNumber] = useState(DEFAULT_PHONE_NUMBER);
  const [refreshKey, setRefreshKey] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [isSavingGoal, setIsSavingGoal] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [goalError, setGoalError] = useState<string | null>(null);
  const currentDate = formatCurrentDate();

  useEffect(() => {
    const abortController = new AbortController();

    async function loadDashboardData() {
      setIsLoading(true);
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
      } finally {
        if (!abortController.signal.aborted) {
          setIsLoading(false);
        }
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

  function handlePhoneSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const normalizedPhoneNumber = phoneNumberDraft.trim() || DEFAULT_PHONE_NUMBER;
    setPhoneNumberDraft(normalizedPhoneNumber);
    setActivePhoneNumber(normalizedPhoneNumber);
    setRefreshKey((currentKey) => currentKey + 1);
  }

  function handleRefreshClick() {
    setRefreshKey((currentKey) => currentKey + 1);
  }

  const dashboardStatus = loadError
    ? loadError
    : isLoading
      ? `Loading live data for ${activePhoneNumber}...`
      : `Live data loaded for ${activePhoneNumber}`;

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

        <section className="panel control-card" aria-label="Dashboard connection controls">
          <div className="card-title-row">
            <div>
              <p className="section-label">live backend</p>
              <h2>Dashboard source</h2>
            </div>
            <button
              className="secondary-action compact-action"
              type="button"
              onClick={handleRefreshClick}
              disabled={isLoading}
            >
              Refresh
            </button>
          </div>
          <form className="phone-form" onSubmit={handlePhoneSubmit}>
            <label>
              Demo phone number
              <input
                inputMode="tel"
                type="text"
                value={phoneNumberDraft}
                onChange={(event) => setPhoneNumberDraft(event.target.value)}
                placeholder={DEFAULT_PHONE_NUMBER}
              />
            </label>
            <button className="primary-action compact-action" type="submit" disabled={isLoading}>
              Load dashboard
            </button>
          </form>
          <p className={loadError ? "status-banner error" : "status-banner"}>{dashboardStatus}</p>
        </section>

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
