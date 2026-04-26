import { formatCurrency, getCategoryTotals, type Prediction, type Transaction } from "../demoLogic";

type WeeklyTrendsProps = {
  transactions: Transaction[];
  prediction: Prediction | null;
};

const defaultTrends = [
  {
    label: "Transactions",
    value: "0",
    copy: "Connect a Plaid sandbox bank to populate the workspace.",
  },
  {
    label: "Prediction",
    value: "Pending",
    copy: "The engine needs a few repeated bank transactions before it forecasts the next habit.",
  },
  {
    label: "Goal impact",
    value: "$0",
    copy: "Once a forecast appears, this card will estimate the weekly savings upside from real bank activity.",
  },
];

function WeeklyTrends({ transactions, prediction }: WeeklyTrendsProps) {
  const topCategory = getCategoryTotals(transactions)[0];
  const totalSpend = transactions.reduce((sum, transaction) => sum + transaction.amount, 0);
  const trends =
    transactions.length === 0
      ? defaultTrends
      : [
          {
            label: topCategory ? topCategory.category : "Transactions",
            value: topCategory ? `${topCategory.percent}%` : `${transactions.length}`,
            copy: topCategory
              ? "Largest current share of recent spending."
              : "Recent purchases are starting to populate the dashboard.",
          },
          prediction
            ? {
                label: prediction.category,
                value: `${prediction.probability}%`,
                copy: "Most predictable habit by time of day.",
              }
            : {
                label: "Prediction",
                value: "Learning",
                copy: "A few more repeated transactions will unlock the first forecast.",
              },
          {
            label: "Recent spend",
            value: formatCurrency(totalSpend),
            copy: "Current total across the loaded transaction history.",
          },
        ];

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
