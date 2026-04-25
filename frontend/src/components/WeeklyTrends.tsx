import { getCategoryTotals, type Prediction, type Transaction } from "../demoLogic";

type WeeklyTrendsProps = {
  transactions: Transaction[];
  prediction: Prediction;
};

const defaultTrends = [
  {
    label: "Food",
    value: "+18%",
    copy: "Up this week, mostly from delivery and coffee.",
  },
  {
    label: "Transportation",
    value: "Flat",
    copy: "Rides stayed steady compared with last week.",
  },
  {
    label: "Coffee",
    value: "74%",
    copy: "Most predictable habit by time of day.",
  },
];

function WeeklyTrends({ transactions, prediction }: WeeklyTrendsProps) {
  const topCategory = getCategoryTotals(transactions)[0];
  const trends = topCategory
    ? [
        {
          label: topCategory.category,
          value: `${topCategory.percent}%`,
          copy: "Largest current share of recent spending.",
        },
        {
          label: prediction.category,
          value: `${prediction.probability}%`,
          copy: "Most predictable habit by time of day.",
        },
        {
          label: "Goal impact",
          value: `$${Math.round(prediction.amount * 5)}`,
          copy: "Potential weekly savings from skipping this habit.",
        },
      ]
    : defaultTrends;

  return (
    <section className="panel trend-card" aria-labelledby="trends-title">
      <p className="section-label">weekly trends</p>
      <h2 id="trends-title">Signals</h2>
      <div className="trend-grid">
        {trends.map((trend) => (
          <article key={trend.label}>
            <span>{trend.label}</span>
            <strong>{trend.value}</strong>
            <p>{trend.copy}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

export default WeeklyTrends;
