import { formatCurrency, type Goal, type Prediction } from "../demoLogic";

type PredictionCardProps = {
  prediction: Prediction | null;
  goal: Goal | null;
};

function PredictionCard({ prediction, goal }: PredictionCardProps) {
  if (prediction === null) {
    return (
      <section className="panel prediction-card" aria-labelledby="prediction-title">
        <div>
          <p className="section-label">next likely spend</p>
          <h2 id="prediction-title">Not enough history yet</h2>
        </div>
        <p className="prediction-empty-copy">
          Keep logging repeat purchases for the selected phone number and the forecast card will
          fill in automatically.
        </p>
        <div className="skip-impact">
          <p>What unlocks predictions?</p>
          <div className="skip-impact-grid">
            <div>
              <span>Repeat category</span>
              <strong>3+ logs</strong>
              <small>for the same habit</small>
            </div>
            <div>
              <span>Consistent timing</span>
              <strong>Daily rhythm</strong>
              <small>helps the model find a window</small>
            </div>
            <div>
              <span>Goal context</span>
              <strong>{goal?.name ?? "Set a goal"}</strong>
              <small>makes future nudges more useful</small>
            </div>
          </div>
        </div>
      </section>
    );
  }

  const skipOptions = [1, 3, 5];
  const goalName = goal?.name ?? "your goal";

  return (
    <section className="panel prediction-card" aria-labelledby="prediction-title">
      <div>
        <p className="section-label">next likely spend</p>
        <h2 id="prediction-title">{prediction.category}</h2>
      </div>
      <div className="prediction-grid">
        <div>
          <span>Window</span>
          <strong>{prediction.window}</strong>
        </div>
        <div>
          <span>Probability</span>
          <strong>{prediction.probability}%</strong>
        </div>
        <div>
          <span>Typical spend</span>
          <strong>{formatCurrency(prediction.amount)}</strong>
        </div>
      </div>
      <div className="skip-impact">
        <p>What if I skip?</p>
        <div className="skip-impact-grid">
          {skipOptions.map((times) => (
            <div key={times}>
              <span>{times}x this week</span>
              <strong>{formatCurrency(prediction.amount * times)}</strong>
              <small>toward {goalName}</small>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

export default PredictionCard;
