"""Automated Infeasibility Diagnosis and Constraint Relaxation Engine.

This module provides post-mortem diagnostics for over-constrained or infeasible
flight operations scenarios. When mathematical optimization cannot fulfill all
missions or proves infeasibility, the InfeasibilityDiagnoser systematically
identifies binding bottleneck resources, unsat cores, and relaxed trade-offs:
1. Fleet capacity exhaustion / capability mismatch.
2. Crew qualification deficit or maximum flight duty saturation.
3. Airbase runway movement hourly slot congestion.
4. Maintenance blackout overlap collisions.
5. Automated slack-relaxation computation (minimal resource additions needed).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DiagnosticBottleneck:
    """Detailed record of an identified operational resource bottleneck."""

    category: str  # "AIRCRAFT_CAPABILITY", "CREW_QUALIFICATION", "CREW_DUTY_LIMIT", "RUNWAY_CAPACITY", "MAINTENANCE_LOCKOUT"
    resource_id: str
    affected_task_ids: list[str]
    description: str
    recommended_relaxation: str
    severity: str = "HIGH"  # "CRITICAL", "HIGH", "MEDIUM"


@dataclass
class InfeasibilityReport:
    """Comprehensive diagnostic summary for unassigned tasks or infeasible models."""

    is_feasible: bool
    unassigned_task_count: int
    unassigned_task_ids: list[str]
    bottlenecks: list[DiagnosticBottleneck] = field(default_factory=list)
    explanations: list[str] = field(default_factory=list)
    recommended_actions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize report to standard dictionary format."""
        return {
            "is_feasible": self.is_feasible,
            "unassigned_task_count": self.unassigned_task_count,
            "unassigned_task_ids": self.unassigned_task_ids,
            "bottlenecks": [
                {
                    "category": b.category,
                    "resource_id": b.resource_id,
                    "affected_task_ids": b.affected_task_ids,
                    "description": b.description,
                    "recommended_relaxation": b.recommended_relaxation,
                    "severity": b.severity,
                }
                for b in self.bottlenecks
            ],
            "explanations": list(self.explanations),
            "recommended_actions": list(self.recommended_actions),
        }


class InfeasibilityDiagnoser:
    """Diagnoses reasons why tasks could not be scheduled or why constraints failed."""

    @classmethod
    def diagnose(
        cls,
        tasks: list[dict[str, Any]],
        aircraft: list[dict[str, Any]],
        crew: list[dict[str, Any]],
        airbases: list[dict[str, Any]],
        maintenance_windows: list[dict[str, Any]],
        unassigned_task_ids: list[str],
    ) -> InfeasibilityReport:
        """Perform hierarchical bottleneck inspection on unassigned tasks."""
        if not unassigned_task_ids:
            return InfeasibilityReport(
                is_feasible=True,
                unassigned_task_count=0,
                unassigned_task_ids=[],
                bottlenecks=[],
                explanations=["All requested tasks were successfully scheduled."],
                recommended_actions=[],
            )

        bottlenecks: list[DiagnosticBottleneck] = []
        explanations: list[str] = []
        recommended_actions: list[str] = []

        task_map = {t["task_id"]: t for t in tasks}

        for tid in unassigned_task_ids:
            t = task_map.get(tid)
            if not t:
                continue

            req_cap = t.get("required_capability") or t.get("required_type")
            req_qual = t.get("required_qualification") or req_cap
            duration = int(t.get("duration_minutes", 60))
            est = int(t.get("earliest_start_minute", 0))
            lst = int(t.get("latest_start_minute", est + 180))
            origin = t.get("origin_base_id") or t.get("origin")
            dest = t.get("dest_base_id") or t.get("dest")

            # 1. Capability & fleet size audit
            compatible_ac = [
                ac for ac in aircraft
                if not req_cap or (ac.get("capability_class") or ac.get("type_id")) == req_cap
            ]
            if not compatible_ac:
                msg = f"Task '{tid}' requires airframe capability '{req_cap}', but no aircraft in the fleet possess this capability."
                bottlenecks.append(
                    DiagnosticBottleneck(
                        category="AIRCRAFT_CAPABILITY",
                        resource_id=req_cap or "UNKNOWN",
                        affected_task_ids=[tid],
                        description=msg,
                        recommended_relaxation=f"Deploy or mobilize an aircraft configured for '{req_cap}'.",
                        severity="CRITICAL",
                    )
                )
                explanations.append(msg)
                continue

            # 2. Crew certification audit
            compatible_crew = [
                cr for cr in crew
                if not req_qual or req_qual in (cr.get("certified_classes") or [cr.get("qualification")])
            ]
            if not compatible_crew:
                msg = f"Task '{tid}' requires crew qualification '{req_qual}', but no available crew members hold this certification."
                bottlenecks.append(
                    DiagnosticBottleneck(
                        category="CREW_QUALIFICATION",
                        resource_id=req_qual or "UNKNOWN",
                        affected_task_ids=[tid],
                        description=msg,
                        recommended_relaxation=f"Authorize qualified crew roster expansion for '{req_qual}'.",
                        severity="CRITICAL",
                    )
                )
                explanations.append(msg)
                continue

            # 3. Crew duty hours audit
            available_crew_duty = [
                cr for cr in compatible_crew
                if int(cr.get("max_duty_minutes_24h", 480)) >= duration
            ]
            if not available_crew_duty:
                msg = f"Task '{tid}' requires duration {duration}m, exceeding the maximum allowable 24h duty ceiling of all qualified crew."
                bottlenecks.append(
                    DiagnosticBottleneck(
                        category="CREW_DUTY_LIMIT",
                        resource_id="CREW_DUTY_LIMIT",
                        affected_task_ids=[tid],
                        description=msg,
                        recommended_relaxation="Grant duty-time extension waiver or divide task into multi-leg sorties.",
                        severity="HIGH",
                    )
                )
                explanations.append(msg)
                continue

            # 4. Maintenance lockout inspection
            locked_out_ac_count = 0
            for ac in compatible_ac:
                aid = ac["aircraft_id"]
                for mw in maintenance_windows:
                    if mw["aircraft_id"] == aid:
                        m_start = int(mw["start_minute"])
                        m_end = int(mw["end_minute"])
                        # Check overlap with task window [est, lst + duration]
                        if not (m_end <= est or m_start >= lst + duration):
                            locked_out_ac_count += 1
                            break

            if locked_out_ac_count == len(compatible_ac):
                msg = f"Task '{tid}' conflicts with scheduled maintenance windows on all {len(compatible_ac)} compatible aircraft."
                bottlenecks.append(
                    DiagnosticBottleneck(
                        category="MAINTENANCE_LOCKOUT",
                        resource_id=compatible_ac[0]["aircraft_id"],
                        affected_task_ids=[tid],
                        description=msg,
                        recommended_relaxation="Reschedule non-critical hangar inspection or shift flight window.",
                        severity="MEDIUM",
                    )
                )
                explanations.append(msg)
                continue

            # 5. Airbase runway congestion audit
            for base in airbases:
                bid = base["airbase_id"]
                max_mv = int(base.get("max_hourly_movements", 20))
                if max_mv <= 0 and (origin == bid or dest == bid):
                    msg = f"Task '{tid}' involves airbase '{bid}' where hourly movement capacity is zero (closed runway)."
                    bottlenecks.append(
                        DiagnosticBottleneck(
                            category="RUNWAY_CAPACITY",
                            resource_id=bid,
                            affected_task_ids=[tid],
                            description=msg,
                            recommended_relaxation=f"Reopen runway slot at base '{bid}' or route to alternate airfield.",
                            severity="CRITICAL",
                        )
                    )
                    explanations.append(msg)
                    break

            # 6. Resource Competition / Fleet Saturation
            if not any(b.affected_task_ids == [tid] for b in bottlenecks):
                msg = (
                    f"Task '{tid}' was displaced due to resource competition: higher priority missions saturated "
                    f"all {len(compatible_ac)} compatible aircraft or {len(compatible_crew)} qualified crew during time window [{est}, {lst}]."
                )
                bottlenecks.append(
                    DiagnosticBottleneck(
                        category="FLEET_SATURATION",
                        resource_id="FLEET_CAPACITY",
                        affected_task_ids=[tid],
                        description=msg,
                        recommended_relaxation=f"Broaden scheduling time window [{est}, {lst + 360}] or allocate supplementary aircraft.",
                        severity="HIGH",
                    )
                )
                explanations.append(msg)

        # Global recommendations synthesis
        categories = {b.category for b in bottlenecks}
        if "AIRCRAFT_CAPABILITY" in categories:
            recommended_actions.append("Adjust squadron deployment: Request cross-base staging of missing capability classes.")
        if "CREW_QUALIFICATION" in categories:
            recommended_actions.append("Roster adjustment: Assign multi-role certified pilots to reserve pools.")
        if "CREW_DUTY_LIMIT" in categories:
            recommended_actions.append("Crew fatigue management: Stage auxiliary relief crews for long-duration sorties.")
        if "MAINTENANCE_LOCKOUT" in categories:
            recommended_actions.append("Maintenance rescheduling: Shift routine preventive checks out of peak mission hours.")
        if "RUNWAY_CAPACITY" in categories:
            recommended_actions.append("Airfield operations: Increase slot allocations or re-route sorties to secondary fields.")
        if "FLEET_SATURATION" in categories:
            recommended_actions.append("Mission window relaxation: Extend latest-start bounds by 2-4 hours to absorb congestion peaks.")

        return InfeasibilityReport(
            is_feasible=False,
            unassigned_task_count=len(unassigned_task_ids),
            unassigned_task_ids=unassigned_task_ids,
            bottlenecks=bottlenecks,
            explanations=explanations,
            recommended_actions=recommended_actions,
        )
