import { formatCurrency, type Goal, type Prediction } from "../demoLogic";
import type { NudgeFrequency, NudgeTone } from "./NudgeSettings";

type SmsPreviewProps = {
  prediction: Prediction | null;
  goal: Goal | null;
  tone: NudgeTone;
  frequency: NudgeFrequency;
};

function buildMessage(prediction: Prediction | null, goal: Goal | null, tone: NudgeTone) {
  if (prediction === null) {
    return "Connect a bank and let a few repeat purchases arrive. The live nudge preview will appear once the model sees a pattern.";
  }

  const amount = formatCurrency(prediction.amount);
  const goalName = goal?.name ?? "your goal";

  if (tone === "Direct") {
    return `${prediction.category} is likely soon. Skip it and move ${amount} closer to ${goalName}.`;
  }

  if (tone === "Funny") {
    return `${prediction.category} is calling again. Let it go to voicemail and keep ${amount} for ${goalName}.`;
  }

  return `You may grab ${prediction.category.toLowerCase()} soon. Skipping today puts ${amount} toward ${goalName}.`;
}

function SmsPreview({ prediction, goal, tone, frequency }: SmsPreviewProps) {
  return (
    <section className="sms-preview" aria-labelledby="sms-title">
      <p className="section-label" id="sms-title">
        plaid-powered nudge preview
      </p>
      <div className="sms-meta">
        <span>{tone} tone</span>
        <span>{frequency} frequency</span>
      </div>
      <div className="sms-bubble">{buildMessage(prediction, goal, tone)}</div>
    </section>
  );
}

export default SmsPreview;
