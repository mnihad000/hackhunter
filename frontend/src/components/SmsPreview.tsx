import { formatCurrency, type Goal, type Prediction } from "../demoLogic";
import type { NudgeFrequency, NudgeTone } from "./NudgeSettings";

type SmsPreviewProps = {
  prediction: Prediction;
  goal: Goal;
  tone: NudgeTone;
  frequency: NudgeFrequency;
};

function buildMessage(prediction: Prediction, goal: Goal, tone: NudgeTone) {
  const amount = formatCurrency(prediction.amount);

  if (tone === "Direct") {
    return `${prediction.category} is likely soon. Skip it and move ${amount} closer to ${goal.name}.`;
  }

  if (tone === "Funny") {
    return `${prediction.category} is calling again. Let it go to voicemail and keep ${amount} for ${goal.name}.`;
  }

  return `You may grab ${prediction.category.toLowerCase()} soon. Skipping today puts ${amount} toward ${goal.name}.`;
}

function SmsPreview({ prediction, goal, tone, frequency }: SmsPreviewProps) {
  return (
    <section className="sms-preview" aria-labelledby="sms-title">
      <p className="section-label" id="sms-title">
        sms nudge preview
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
