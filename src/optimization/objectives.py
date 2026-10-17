"""Objective Function Builder with Integer Scaling for CP-SAT.

This module formulates the multi-objective utility function for CP-SAT,
scaling continuous metrics (probabilities, penalties) to integer domains:
1. Priority-weighted task fulfillment reward.
2. Linear delay penalties for departures beyond earliest preferred time.
3. Airframe failure risk mitigation penalty.
4. Schedule churn penalties for counterfactual replanning.
"""

from __future__ import annotations

from typing import Any

from ortools.sat.python import cp_model

from src.optimization.constraints import ConstraintBuilder
from src.optimization.solver_config import SolverConfig


class ObjectiveBuilder:
    """Builds integer-scaled composite objective functions for CP-SAT."""

    def __init__(self, model: cp_model.CpModel, constraints: ConstraintBuilder) -> None:
        self.model = model
        self.c = constraints

    def build_composite_objective(
        self,
        tasks: list[dict[str, Any]],
        aircraft: list[dict[str, Any]],
        config: SolverConfig,
        risk_profile: dict[str, float] | None = None,
        baseline_assignments: dict[str, str] | None = None,
    ) -> None:
        """Construct composite objective and maximize in CP-SAT model.

        Objective: Maximize Reward(Fulfillment) - Penalty(Delay) - Penalty(Risk) - Penalty(Churn)
        """
        objective_terms = []

        # 1. Task Fulfillment Reward: sum(priority * u[task])
        for t in tasks:
            tid = t["task_id"]
            priority = int(t.get("priority", 50))
            scaled_reward = priority * config.weight_priority
            objective_terms.append(scaled_reward * self.c.u[tid])

        # 2. Schedule Delay Penalty: -sum(weight_delay * delay[task])
        for t in tasks:
            tid = t["task_id"]
            delay_penalty = config.weight_delay_minute
            objective_terms.append(-delay_penalty * self.c.delay_vars[tid])

        # 3. Aircraft Failure Risk Penalty: -sum(scaled_risk * x[task, aircraft])
        if risk_profile:
            for t in tasks:
                tid = t["task_id"]
                for ac in aircraft:
                    aid = ac["aircraft_id"]
                    prob_fail = float(risk_profile.get(aid, 0.0))
                    # Scale risk: floor(weight_risk * prob_fail)
                    scaled_risk = int(config.weight_risk * prob_fail)
                    if scaled_risk > 0:
                        objective_terms.append(-scaled_risk * self.c.x[(tid, aid)])

        # 4. Schedule Churn Penalty (Counterfactual replanning): -weight_churn * (1 if reassigned)
        if baseline_assignments:
            for t in tasks:
                tid = t["task_id"]
                prev_aid = baseline_assignments.get(tid)
                if prev_aid:
                    for ac in aircraft:
                        aid = ac["aircraft_id"]
                        if aid != prev_aid:
                            # Reassignment penalty applies if newly assigned to different aircraft
                            objective_terms.append(-config.weight_churn * self.c.x[(tid, aid)])

        # Set maximization objective on CP-SAT model
        self.model.Maximize(sum(objective_terms))
