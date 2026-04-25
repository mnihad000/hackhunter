import { useEffect, useState } from "react";
import {
  formatCurrency,
  getGoalProgress,
  getRemainingGoalAmount,
  getGoalStatus,
  type Goal,
} from "../demoLogic";

type GoalProgressProps = {
  goal: Goal;
  onGoalChange: (goal: Goal) => void;
};

function GoalProgress({ goal, onGoalChange }: GoalProgressProps) {
  const [savedDraft, setSavedDraft] = useState(String(goal.saved));
  const [targetDraft, setTargetDraft] = useState(String(goal.target));
  const progress = getGoalProgress(goal);
  const remaining = getRemainingGoalAmount(goal);
  const goalStatus = getGoalStatus(goal);
  const goalMessage =
    goalStatus === "overfunded"
      ? "Congrats, you've got more than enough money."
      : goalStatus === "met"
        ? "You are there."
        : `You are ${formatCurrency(remaining)} away.`;

  useEffect(() => {
    setSavedDraft(String(goal.saved));
  }, [goal.saved]);

  useEffect(() => {
    setTargetDraft(String(goal.target));
  }, [goal.target]);

  const parseMoneyInput = (value: string, minimum: number) => {
    const parsed = Number(value);

    if (!Number.isFinite(parsed)) {
      return null;
    }

    return Math.max(minimum, parsed);
  };

  return (
    <section className="panel goal-card" aria-labelledby="goal-title">
      <div className="goal-heading">
        <div>
          <p className="section-label">goal progress</p>
          <h2 id="goal-title">{goal.name}</h2>
        </div>
        <strong>{formatCurrency(remaining)}</strong>
      </div>
      <div className="progress-track" aria-label={`${progress}% saved`}>
        <span style={{ width: `${progress}%` }} />
      </div>
      <p className="goal-copy">
        {formatCurrency(goal.saved)} saved of {formatCurrency(goal.target)}. {goalMessage}
      </p>
      <div className="goal-editor" aria-label="Edit savings goal">
        <label>
          Goal
          <input
            type="text"
            value={goal.name}
            onChange={(event) => onGoalChange({ ...goal, name: event.target.value })}
          />
        </label>
        <label>
          Saved
          <input
            inputMode="decimal"
            type="text"
            value={savedDraft}
            onBlur={() => setSavedDraft(String(goal.saved))}
            onChange={(event) => {
              const nextValue = event.target.value;
              const parsed = parseMoneyInput(nextValue, 0);

              setSavedDraft(nextValue);

              if (parsed !== null) {
                onGoalChange({ ...goal, saved: parsed });
              }
            }}
          />
        </label>
        <label>
          Target
          <input
            inputMode="decimal"
            type="text"
            value={targetDraft}
            onBlur={() => setTargetDraft(String(goal.target))}
            onChange={(event) => {
              const nextValue = event.target.value;
              const parsed = parseMoneyInput(nextValue, 1);

              setTargetDraft(nextValue);

              if (parsed !== null) {
                onGoalChange({ ...goal, target: parsed });
              }
            }}
          />
        </label>
      </div>
    </section>
  );
}

export default GoalProgress;
