import { formatCurrency, getCategoryTotals, type Transaction } from "../demoLogic";

type SpendingPieChartProps = {
  transactions: Transaction[];
  selectedCategory: string | null;
  onSelectCategory: (category: string | null) => void;
};

const categoryColors: Record<string, string> = {
  Food: "#36b37e",
  Transportation: "#4f8cff",
  Entertainment: "#9b6bff",
  Shopping: "#f5a623",
  Other: "#8c9a95",
};

const categoryInsights: Record<string, string> = {
  Food: "Most food spending happens after 7 PM, when delivery temptation is highest.",
  Transportation: "Transportation is steady this week, with rides clustered around evening plans.",
  Entertainment: "Entertainment is small but easy to trim when a goal needs a final push.",
  Shopping: "Shopping is the most flexible category in this sample, so it is a good place to pause.",
};

function polarToCartesian(center: number, radius: number, angleInDegrees: number) {
  const angleInRadians = ((angleInDegrees - 90) * Math.PI) / 180;

  return {
    x: center + radius * Math.cos(angleInRadians),
    y: center + radius * Math.sin(angleInRadians),
  };
}

function describeArc(startPercent: number, endPercent: number) {
  const center = 50;
  const outerRadius = 48;
  const innerRadius = 25;
  const startAngle = (startPercent / 100) * 360;
  const endAngle = (endPercent / 100) * 360;
  const largeArcFlag = endAngle - startAngle <= 180 ? "0" : "1";
  const outerStart = polarToCartesian(center, outerRadius, endAngle);
  const outerEnd = polarToCartesian(center, outerRadius, startAngle);
  const innerStart = polarToCartesian(center, innerRadius, startAngle);
  const innerEnd = polarToCartesian(center, innerRadius, endAngle);

  return [
    `M ${outerStart.x} ${outerStart.y}`,
    `A ${outerRadius} ${outerRadius} 0 ${largeArcFlag} 0 ${outerEnd.x} ${outerEnd.y}`,
    `L ${innerStart.x} ${innerStart.y}`,
    `A ${innerRadius} ${innerRadius} 0 ${largeArcFlag} 1 ${innerEnd.x} ${innerEnd.y}`,
    "Z",
  ].join(" ");
}

function SpendingPieChart({
  transactions,
  selectedCategory,
  onSelectCategory,
}: SpendingPieChartProps) {
  const total = transactions.reduce((sum, transaction) => sum + transaction.amount, 0);
  const categoryTotals = getCategoryTotals(transactions);

  let runningTotal = 0;
  const segments = categoryTotals.map(({ category, amount }) => {
      const start = (runningTotal / total) * 100;
      runningTotal += amount;
      const end = (runningTotal / total) * 100;
      const color = categoryColors[category] ?? categoryColors.Other;
      const isSelected = selectedCategory === category;

      return { category, amount, start, end, color, isSelected };
    });

  const selectedAmount =
    segments.find((segment) => segment.category === selectedCategory)?.amount ?? total;

  return (
    <section className="panel spending-card" aria-labelledby="spending-title">
      <div className="card-title-row">
        <div>
          <p className="section-label">purchase breakdown</p>
          <h2 id="spending-title">Categories</h2>
        </div>
        {selectedCategory && (
          <button className="text-action" type="button" onClick={() => onSelectCategory(null)}>
            All
          </button>
        )}
      </div>

      {segments.length === 0 ? (
        <p className="empty-copy">Transactions will appear here once a purchase is logged.</p>
      ) : (
      <div className="spending-chart-layout">
        <div
          className="pie-chart"
          aria-label={`Spending by category, total ${formatCurrency(total)}`}
          role="img"
        >
          <svg viewBox="0 0 100 100" aria-hidden="true" focusable="false">
            {segments.map((segment) => (
              <path
                className={segment.isSelected ? "pie-slice active" : "pie-slice"}
                d={describeArc(segment.start, segment.end)}
                fill={selectedCategory && !segment.isSelected ? "#d6dfdb" : segment.color}
                key={segment.category}
                onClick={() => onSelectCategory(segment.isSelected ? null : segment.category)}
              />
            ))}
          </svg>
          <button
            className="pie-center"
            type="button"
            onClick={() => onSelectCategory(null)}
            aria-label="Show all categories"
          >
            <span>{selectedCategory ?? "Total"}</span>
            <strong>{formatCurrency(selectedAmount)}</strong>
          </button>
        </div>

        <ul className="category-list">
          {segments.map((segment) => {
            const percent = Math.round((segment.amount / total) * 100);

            return (
              <li key={segment.category}>
                <span className="category-swatch" style={{ background: segment.color }} />
                <button
                  className={segment.isSelected ? "category-button active" : "category-button"}
                  type="button"
                  onClick={() =>
                    onSelectCategory(segment.isSelected ? null : segment.category)
                  }
                >
                  <strong>{segment.category}</strong>
                  <span>
                    {percent}% - {formatCurrency(segment.amount)}
                  </span>
                </button>
              </li>
            );
          })}
        </ul>
      </div>
      )}
      <p className="category-insight">
        {selectedCategory
          ? categoryInsights[selectedCategory] ?? "This category is worth a closer look."
          : "Tap a category to filter transactions and see a quick behavior insight."}
      </p>
    </section>
  );
}

export default SpendingPieChart;
