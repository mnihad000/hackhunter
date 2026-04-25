type LandingPageProps = {
  onGetStarted: () => void;
};

function LandingPage({ onGetStarted }: LandingPageProps) {
  return (
    <main className="landing-page" aria-labelledby="landing-title">
      <div className="landing-copy">
        <p className="landing-kicker">sms-first financial guidance</p>
        <h1 id="landing-title">Spendly</h1>
        <p className="landing-summary">
          A real-time spending companion that predicts everyday purchases and nudges
          you before small habits pull money away from bigger goals.
        </p>
        <div className="landing-status" aria-label="Spendly status">
          <span>Predictive spending companion</span>
          <strong>96% signal confidence</strong>
        </div>
        <div className="landing-actions">
          <button className="primary-action" type="button" onClick={onGetStarted}>
            Get Started
          </button>
        </div>
      </div>
    </main>
  );
}

export default LandingPage;
