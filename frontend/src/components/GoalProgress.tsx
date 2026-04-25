import type { Goal } from "./Dashboard";

type GoalProgressProps = {
  goal: Goal;
  onGoalChange: (goal: Goal) => void;
};

function GoalProgress({ goal, onGoalChange }: GoalProgressProps) {
  const progress = Math.min(100, Math.round((goal.saved / goal.target) * 100));
  const remaining = Math.max(0, goal.target - goal.saved);

  return (
    <section className="panel goal-card" aria-labelledby="goal-title">
      <div className="goal-heading">
        <div>
          <p className="section-label">goal progress</p>
          <h2 id="goal-title">{goal.name}</h2>
        </div>
        <strong>${remaining}</strong>
      </div>
      <div className="progress-track" aria-label={`${progress}% saved`}>
        <span style={{ width: `${progress}%` }} />
      </div>
      <p className="goal-copy">
        ${goal.saved} saved of ${goal.target}. You are {remaining === 0 ? "there" : `$${remaining} away`}.
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
          Target
          <input
            min="1"
            type="number"
            value={goal.target}
            onChange={(event) =>
              onGoalChange({ ...goal, target: Math.max(1, Number(event.target.value) || 1) })
            }
          />
        </label>
      </div>
    </section>
  );
}

export default GoalProgress;
