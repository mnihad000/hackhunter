import { type FormEvent, useEffect, useState } from "react";
import {
  formatCurrency,
  getGoalProgress,
  getGoalStatus,
  getRemainingGoalAmount,
  type Goal,
} from "../demoLogic";

type GoalProgressProps = {
  goal: Goal | null;
  isSaving: boolean;
  saveError: string | null;
  onGoalSave: (goal: Goal) => void | Promise<void>;
};

const fallbackGoal: Goal = {
  name: "Bike fund",
  target: 250,
  saved: 0,
};

function GoalProgress({ goal, isSaving, saveError, onGoalSave }: GoalProgressProps) {
  const baseGoal = goal ?? fallbackGoal;
  const [nameDraft, setNameDraft] = useState(baseGoal.name);
  const [savedDraft, setSavedDraft] = useState(String(baseGoal.saved));
  const [targetDraft, setTargetDraft] = useState(String(baseGoal.target));

  useEffect(() => {
    setNameDraft(baseGoal.name);
    setSavedDraft(String(baseGoal.saved));
    setTargetDraft(String(baseGoal.target));
  }, [baseGoal.name, baseGoal.saved, baseGoal.target]);

  function parseMoneyInput(value: string, minimum: number) {
    const parsed = Number(value);

    if (!Number.isFinite(parsed)) {
      return null;
    }

    return Math.max(minimum, parsed);
  }

  const parsedSaved = parseMoneyInput(savedDraft, 0);
  const parsedTarget = parseMoneyInput(targetDraft, 1);
  const previewGoal: Goal = {
    name: nameDraft.trim() || fallbackGoal.name,
    saved: parsedSaved ?? baseGoal.saved,
    target: parsedTarget ?? baseGoal.target,
  };
  const progress = getGoalProgress(previewGoal);
  const remaining = getRemainingGoalAmount(previewGoal);
  const goalStatus = getGoalStatus(previewGoal);
  const canSave = nameDraft.trim().length > 0 && parsedSaved !== null && parsedTarget !== null;
  const goalMessage =
    goalStatus === "overfunded"
      ? "Congrats, you've got more than enough money."
      : goalStatus === "met"
        ? "You are there."
        : `You are ${formatCurrency(remaining)} away.`;

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canSave) {
      return;
    }

    void onGoalSave(previewGoal);
  }

  return (
    <section className="panel goal-card" aria-labelledby="goal-title">
      <div className="goal-heading">
        <div>
          <p className="section-label">goal progress</p>
          <h2 id="goal-title">{goal ? previewGoal.name : "Set your first goal"}</h2>
        </div>
        <strong>{formatCurrency(remaining)}</strong>
      </div>
      <div className="progress-track" aria-label={`${progress}% saved`}>
        <span style={{ width: `${progress}%` }} />
      </div>
      <p className="goal-copy">
        {formatCurrency(previewGoal.saved)} saved of {formatCurrency(previewGoal.target)}.{" "}
        {goal ? goalMessage : "Create a goal to turn nudges into something concrete."}
      </p>
      <form className="goal-editor" aria-label="Edit savings goal" onSubmit={handleSubmit}>
        <label>
          Goal
          <input
            type="text"
            value={nameDraft}
            onChange={(event) => setNameDraft(event.target.value)}
          />
        </label>
        <label>
          Saved
          <input
            inputMode="decimal"
            type="text"
            value={savedDraft}
            onChange={(event) => setSavedDraft(event.target.value)}
          />
        </label>
        <label>
          Target
          <input
            inputMode="decimal"
            type="text"
            value={targetDraft}
            onChange={(event) => setTargetDraft(event.target.value)}
          />
        </label>
        <button className="primary-action compact-action goal-save-action" type="submit" disabled={!canSave || isSaving}>
          {isSaving ? "Saving..." : goal ? "Save goal" : "Create goal"}
        </button>
      </form>
      {saveError && <p className="status-banner error">{saveError}</p>}
    </section>
  );
}

export default GoalProgress;
