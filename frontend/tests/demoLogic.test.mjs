import assert from "node:assert/strict";
import {
  getCategoryTotals,
  getGoalProgress,
  getRemainingGoalAmount,
  getGoalStatus,
  initialGoal,
  initialTransactions,
} from "../src/demoLogic.ts";

assert.equal(getGoalProgress(initialGoal), 83);
assert.equal(getRemainingGoalAmount(initialGoal), 42);
assert.equal(getGoalStatus(initialGoal), "behind");

const exactGoal = { name: "Bike fund", target: 250, saved: 250 };
assert.equal(getGoalProgress(exactGoal), 100);
assert.equal(getRemainingGoalAmount(exactGoal), 0);
assert.equal(getGoalStatus(exactGoal), "met");

const overfundedGoal = { name: "Bike fund", target: 250, saved: 300 };
assert.equal(getGoalProgress(overfundedGoal), 100);
assert.equal(getRemainingGoalAmount(overfundedGoal), 0);
assert.equal(getGoalStatus(overfundedGoal), "overfunded");

const [topCategory] = getCategoryTotals(initialTransactions);
assert.equal(topCategory.category, "Food");
assert.equal(topCategory.percent, 39);

console.log("demoLogic assertions passed");
