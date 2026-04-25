const trends = [
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

function WeeklyTrends() {
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
