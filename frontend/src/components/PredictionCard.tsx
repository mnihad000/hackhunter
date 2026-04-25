import type { Goal } from "./Dashboard";

type Prediction = {
  category: string;
  window: string;
  probability: number;
  amount: number;
};

type PredictionCardProps = {
  prediction: Prediction;
  goal: Goal;
};

function formatCurrency(amount: number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(amount);
}

function PredictionCard({ prediction, goal }: PredictionCardProps) {
  const skipOptions = [1, 3, 5];

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
              <small>toward {goal.name}</small>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

export default PredictionCard;
