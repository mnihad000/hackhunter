import { type FormEvent, useEffect, useMemo, useState } from "react";
import {
  DEFAULT_PHONE_NUMBER,
  createPlaidLinkToken,
  exchangePlaidPublicToken,
  fetchGoal,
  fetchPrediction,
  fetchTransactions,
  saveGoal,
  syncPlaidTransactions,
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

type PlaidWorkspaceState = {
  importedCount: number;
  institutionName: string | null;
  isLinked: boolean;
  lastRemovedCount: number;
  lastSyncedAt: string | null;
};

type PlaidSuccessMetadata = {
  institution?: {
    name?: string | null;
  } | null;
};

type PlaidHandler = {
  open: () => void;
  destroy?: () => void;
};

declare global {
  interface Window {
    Plaid?: {
      create: (config: {
        token: string;
        onSuccess: (publicToken: string, metadata: PlaidSuccessMetadata) => void;
        onExit?: (error: { error_message?: string } | null) => void;
      }) => PlaidHandler;
    };
  }
}

let plaidScriptPromise: Promise<void> | null = null;

function getWorkspaceStorageKey(phoneNumber: string) {
  return `spendly:plaid:${phoneNumber.trim() || DEFAULT_PHONE_NUMBER}`;
}

function readPlaidWorkspace(phoneNumber: string): PlaidWorkspaceState {
  if (typeof window === "undefined") {
    return {
      importedCount: 0,
      institutionName: null,
      isLinked: false,
      lastRemovedCount: 0,
      lastSyncedAt: null,
    };
  }

  try {
    const rawValue = window.localStorage.getItem(getWorkspaceStorageKey(phoneNumber));
    if (!rawValue) {
      return {
        importedCount: 0,
        institutionName: null,
        isLinked: false,
        lastRemovedCount: 0,
        lastSyncedAt: null,
      };
    }

    const parsed = JSON.parse(rawValue) as Partial<PlaidWorkspaceState>;
    return {
      importedCount: typeof parsed.importedCount === "number" ? parsed.importedCount : 0,
      institutionName: typeof parsed.institutionName === "string" ? parsed.institutionName : null,
      isLinked: parsed.isLinked === true,
      lastRemovedCount: typeof parsed.lastRemovedCount === "number" ? parsed.lastRemovedCount : 0,
      lastSyncedAt: typeof parsed.lastSyncedAt === "string" ? parsed.lastSyncedAt : null,
    };
  } catch {
    return {
      importedCount: 0,
      institutionName: null,
      isLinked: false,
      lastRemovedCount: 0,
      lastSyncedAt: null,
    };
  }
}

function formatLastSync(lastSyncedAt: string | null) {
  if (!lastSyncedAt) {
    return "No sync yet";
  }

  const syncDate = new Date(lastSyncedAt);
  if (Number.isNaN(syncDate.getTime())) {
    return "No sync yet";
  }

  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(syncDate);
}

function loadPlaidScript() {
  if (typeof window === "undefined") {
    return Promise.reject(new Error("Plaid Link is only available in the browser."));
  }
  if (window.Plaid) {
    return Promise.resolve();
  }
  if (plaidScriptPromise) {
    return plaidScriptPromise;
  }

  plaidScriptPromise = new Promise<void>((resolve, reject) => {
    const existingScript = document.querySelector<HTMLScriptElement>('script[data-plaid-link="true"]');
    if (existingScript) {
      existingScript.addEventListener("load", () => resolve(), { once: true });
      existingScript.addEventListener("error", () => reject(new Error("Unable to load Plaid Link.")), {
        once: true,
      });
      return;
    }

    const script = document.createElement("script");
    script.src = "https://cdn.plaid.com/link/v2/stable/link-initialize.js";
    script.async = true;
    script.dataset.plaidLink = "true";
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("Unable to load Plaid Link."));
    document.head.appendChild(script);
  }).catch((error) => {
    plaidScriptPromise = null;
    throw error;
  });

  return plaidScriptPromise;
}

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
  const [plaidWorkspace, setPlaidWorkspace] = useState<PlaidWorkspaceState>(() =>
    readPlaidWorkspace(DEFAULT_PHONE_NUMBER),
  );
  const [refreshKey, setRefreshKey] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [isSavingGoal, setIsSavingGoal] = useState(false);
  const [isPlaidBusy, setIsPlaidBusy] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [goalError, setGoalError] = useState<string | null>(null);
  const [plaidStatus, setPlaidStatus] = useState<string | null>(null);
  const [plaidError, setPlaidError] = useState<string | null>(null);
  const currentDate = formatCurrentDate();

  useEffect(() => {
    setPlaidWorkspace(readPlaidWorkspace(activePhoneNumber));
  }, [activePhoneNumber]);

  function updatePlaidWorkspace(nextState: Partial<PlaidWorkspaceState>) {
    setPlaidWorkspace((currentState) => {
      const mergedState = { ...currentState, ...nextState };
      if (typeof window !== "undefined") {
        window.localStorage.setItem(getWorkspaceStorageKey(activePhoneNumber), JSON.stringify(mergedState));
      }
      return mergedState;
    });
  }

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
        if (message === "User not found.") {
          setLoadError(null);
          setTransactions([]);
          setGoal(null);
          setPrediction(null);
          return;
        }

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
    setPlaidStatus(null);
    setPlaidError(null);
    setRefreshKey((currentKey) => currentKey + 1);
  }

  function handleRefreshClick() {
    setRefreshKey((currentKey) => currentKey + 1);
  }

  async function handleConnectBankClick() {
    setIsPlaidBusy(true);
    setPlaidError(null);
    setPlaidStatus("Creating a secure Plaid session...");

    try {
      const { link_token: linkToken } = await createPlaidLinkToken(activePhoneNumber);
      await loadPlaidScript();
      if (!window.Plaid) {
        throw new Error("Plaid Link failed to initialize.");
      }

      const handler = window.Plaid.create({
        token: linkToken,
        onSuccess: (publicToken, metadata) => {
          void (async () => {
            try {
              const response = await exchangePlaidPublicToken(
                activePhoneNumber,
                publicToken,
                metadata.institution?.name ?? undefined,
              );
              const importedLabel =
                response.imported_count === 1
                  ? "1 transaction"
                  : `${response.imported_count} transactions`;
              updatePlaidWorkspace({
                importedCount: response.imported_count,
                institutionName: response.institution_name ?? null,
                isLinked: true,
                lastRemovedCount: 0,
                lastSyncedAt: new Date().toISOString(),
              });
              setPlaidStatus(
                response.institution_name
                  ? `Connected ${response.institution_name}. Imported ${importedLabel}.`
                  : `Bank connected. Imported ${importedLabel}.`,
              );
              setPlaidError(null);
              setRefreshKey((currentKey) => currentKey + 1);
            } catch (error) {
              const message =
                error instanceof Error ? error.message : "Unable to finish the Plaid connection.";
              setPlaidError(message);
              setPlaidStatus(null);
            } finally {
              setIsPlaidBusy(false);
              handler.destroy?.();
            }
          })();
        },
        onExit: (error) => {
          if (error?.error_message) {
            setPlaidError(error.error_message);
            setPlaidStatus(null);
          } else {
            setPlaidStatus("Plaid connection cancelled.");
          }
          setIsPlaidBusy(false);
          handler.destroy?.();
        },
      });

      handler.open();
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unable to start Plaid Link.";
      setPlaidError(message);
      setPlaidStatus(null);
      setIsPlaidBusy(false);
    }
  }

  async function handlePlaidSyncClick() {
    setIsPlaidBusy(true);
    setPlaidError(null);
    setPlaidStatus("Syncing bank transactions...");

    try {
      const response = await syncPlaidTransactions(activePhoneNumber);
      const importedLabel =
        response.imported_count === 1 ? "1 new transaction" : `${response.imported_count} new transactions`;
      const removedLabel =
        response.removed_count > 0
          ? ` Removed ${response.removed_count} cleared transaction${response.removed_count === 1 ? "" : "s"}.`
          : "";
      updatePlaidWorkspace({
        importedCount: response.imported_count,
        isLinked: true,
        lastRemovedCount: response.removed_count,
        lastSyncedAt: new Date().toISOString(),
      });
      setPlaidStatus(`Bank sync finished: ${importedLabel}.${removedLabel}`.trim());
      setRefreshKey((currentKey) => currentKey + 1);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unable to sync bank data right now.";
      setPlaidError(
        message === "No Plaid account is linked for this phone number."
          ? "Connect a bank before running the next sync."
          : message,
      );
      setPlaidStatus(null);
    } finally {
      setIsPlaidBusy(false);
    }
  }

  const transactionCount = transactions.length;
  const hasImportedData = transactionCount > 0 || plaidWorkspace.isLinked;
  const connectionLabel = plaidWorkspace.isLinked ? "Bank linked" : "Connection needed";
  const institutionLabel = plaidWorkspace.institutionName ?? "No institution connected yet";
  const syncLabel = formatLastSync(plaidWorkspace.lastSyncedAt);
  const importedLabel =
    plaidWorkspace.importedCount > 0
      ? `${plaidWorkspace.importedCount} imported`
      : transactionCount > 0
        ? `${transactionCount} transactions loaded`
        : "No imports yet";
  const summaryCopy = loadError
    ? "The workspace is still available, but one or more dashboard requests need attention."
    : hasImportedData
      ? "Bank activity, goals, and nudge preferences are ready to review in one place."
      : "Use one phone number per workspace, then connect a bank or log repeat purchases to unlock the forecast.";
  const dashboardStatus = loadError
    ? loadError
    : isLoading
      ? `Refreshing the banking workspace for ${activePhoneNumber}...`
      : hasImportedData
        ? `Workspace ready for ${activePhoneNumber}.`
        : `Link a Plaid sandbox bank to populate this workspace.`;

  return (
    <main className="dashboard-page" aria-labelledby="dashboard-title">
      <section className="dashboard-shell">
        <header className="dashboard-header">
          <div>
            <p className="dashboard-kicker">Plaid sandbox workspace</p>
            <h1 id="dashboard-title">{currentDate}</h1>
          </div>
          <button className="secondary-action" type="button" onClick={onBack}>
            Back
          </button>
        </header>

        <div className="dashboard-top-grid">
          <section className="panel summary-card" aria-label="Workspace summary">
            <div className="summary-card-head">
              <div>
                <p className="section-label">overview</p>
                <h2>Daily signal board</h2>
              </div>
              <button
                className="secondary-action compact-action"
                type="button"
                onClick={handleRefreshClick}
                disabled={isLoading || isPlaidBusy}
              >
                Refresh
              </button>
            </div>
            <p className="summary-copy">{summaryCopy}</p>
            <div className="summary-metric-grid">
              <article>
                <span>Status</span>
                <strong>{connectionLabel}</strong>
              </article>
              <article>
                <span>Phone</span>
                <strong>{activePhoneNumber}</strong>
              </article>
              <article>
                <span>Institution</span>
                <strong>{institutionLabel}</strong>
              </article>
              <article>
                <span>Imported</span>
                <strong>{importedLabel}</strong>
              </article>
            </div>
            <form className="phone-form summary-form" onSubmit={handlePhoneSubmit}>
              <label>
                Workspace phone
                <input
                  inputMode="tel"
                  type="text"
                  value={phoneNumberDraft}
                  onChange={(event) => setPhoneNumberDraft(event.target.value)}
                  placeholder={DEFAULT_PHONE_NUMBER}
                />
              </label>
              <button className="primary-action compact-action" type="submit" disabled={isLoading}>
                Open workspace
              </button>
            </form>
            <p className="summary-caption">Last sync {syncLabel}</p>
            <p className={loadError ? "status-banner error" : "status-banner"}>{dashboardStatus}</p>
          </section>

          <section className="panel plaid-import-card" aria-label="Plaid import controls">
            <div className="plaid-import-head">
              <div>
                <p className="section-label">bank connection</p>
                <h2>Plaid import</h2>
                <p className="plaid-import-copy">
                  Use Plaid Link to choose a bank and enter Sandbox credentials.
                </p>
              </div>
              <button
                className="secondary-action compact-action"
                type="button"
                onClick={handlePlaidSyncClick}
                disabled={isLoading || isPlaidBusy}
              >
                {isPlaidBusy ? "Working..." : "Sync"}
              </button>
            </div>
            <div className="plaid-import-actions">
              <button
                className="primary-action compact-action"
                type="button"
                onClick={handleConnectBankClick}
                disabled={isLoading || isPlaidBusy}
              >
                {plaidWorkspace.isLinked ? "Reconnect bank" : "Connect bank"}
              </button>
            </div>
            <div className="plaid-import-meta">
              <span>{institutionLabel}</span>
              <strong>{importedLabel}</strong>
            </div>
            {(plaidError || plaidStatus) && (
              <p className={plaidError ? "status-banner error" : "status-banner"}>
                {plaidError ?? plaidStatus}
              </p>
            )}
          </section>
        </div>

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
