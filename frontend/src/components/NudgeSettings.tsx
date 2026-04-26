export type NudgeTone = "Gentle" | "Direct" | "Funny";
export type NudgeFrequency = "Normal" | "Fewer" | "Quiet";

type NudgeSettingsProps = {
  tone: NudgeTone;
  frequency: NudgeFrequency;
  onToneChange: (tone: NudgeTone) => void;
  onFrequencyChange: (frequency: NudgeFrequency) => void;
};

const tones: NudgeTone[] = ["Gentle", "Direct", "Funny"];
const frequencies: NudgeFrequency[] = ["Normal", "Fewer", "Quiet"];

function NudgeSettings({
  tone,
  frequency,
  onToneChange,
  onFrequencyChange,
}: NudgeSettingsProps) {
  return (
    <section className="panel nudge-card" aria-labelledby="nudge-title">
      <p className="section-label">alert settings</p>
      <h2 id="nudge-title">Preferences</h2>

      <div className="setting-group">
        <span>Tone</span>
        <div className="segmented-control">
          {tones.map((option) => (
            <button
              className={option === tone ? "active" : ""}
              key={option}
              type="button"
              onClick={() => onToneChange(option)}
            >
              {option}
            </button>
          ))}
        </div>
      </div>

      <div className="setting-group">
        <span>Frequency</span>
        <div className="segmented-control">
          {frequencies.map((option) => (
            <button
              className={option === frequency ? "active" : ""}
              key={option}
              type="button"
              onClick={() => onFrequencyChange(option)}
            >
              {option}
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}

export default NudgeSettings;
