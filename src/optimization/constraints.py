"""Constraint Programming Model Constraints Builder for CP-SAT.

This module formulates decision variables and hard physical and regulatory
operational constraints for the Google OR-Tools CP-SAT solver:
1. Unique task fulfillment and allocation.
2. Airframe capability and crew certification compatibility.
3. Aircraft non-overlapping sortie disjunctions with turnaround buffers.
4. Flight crew duty-hour limits and mandatory rest windows.
5. Airbase hourly runway movement slot capacities.
6. Scheduled maintenance blackout lockouts.
"""

from __future__ import annotations

from typing import Any

from ortools.sat.python import cp_model


class ConstraintBuilder:
    """Constructs CP-SAT variables and hard operational constraints."""

    def __init__(self, model: cp_model.CpModel) -> None:
        self.model = model
        self.x: dict[tuple[str, str], cp_model.IntVar] = {}  # (task_id, aircraft_id) -> BoolVar
        self.y: dict[tuple[str, str], cp_model.IntVar] = {}  # (task_id, crew_id) -> BoolVar
        self.u: dict[str, cp_model.IntVar] = {}              # task_id -> BoolVar (fulfilled)
        self.start_vars: dict[str, cp_model.IntVar] = {}     # task_id -> IntVar (start minute)
        self.end_vars: dict[str, cp_model.IntVar] = {}       # task_id -> IntVar (end minute)
        self.delay_vars: dict[str, cp_model.IntVar] = {}     # task_id -> IntVar (delay minute)
        self.aircraft_intervals: dict[str, list[cp_model.IntervalVar]] = {}
        self.crew_intervals: dict[str, list[cp_model.IntervalVar]] = {}

    def build_decision_variables(
        self,
        tasks: list[dict[str, Any]],
        aircraft: list[dict[str, Any]],
        crew: list[dict[str, Any]],
        planning_horizon_minutes: int = 1440,
    ) -> None:
        """Create decision variables for task fulfillment, assignment, and timing."""
        for t in tasks:
            tid = t["task_id"]
            est = int(t.get("earliest_start_minute", 0))
            lst = int(t.get("latest_start_minute", est + 180))
            duration = int(t["duration_minutes"])

            self.u[tid] = self.model.NewBoolVar(f"u_{tid}")
            self.start_vars[tid] = self.model.NewIntVar(est, lst, f"start_{tid}")
            self.end_vars[tid] = self.model.NewIntVar(est + duration, lst + duration, f"end_{tid}")
            self.delay_vars[tid] = self.model.NewIntVar(0, lst - est, f"delay_{tid}")

            # Define duration constraint: end = start + duration
            self.model.Add(self.end_vars[tid] == self.start_vars[tid] + duration)
            # Define delay: delay = start - earliest_start
            self.model.Add(self.delay_vars[tid] == self.start_vars[tid] - est)

            # Assignment variables: x[task, aircraft]
            for ac in aircraft:
                aid = ac["aircraft_id"]
                self.x[(tid, aid)] = self.model.NewBoolVar(f"x_{tid}_{aid}")

            # Assignment variables: y[task, crew]
            for cr in crew:
                cid = cr["crew_id"]
                self.y[(tid, cid)] = self.model.NewBoolVar(f"y_{tid}_{cid}")

        for ac in aircraft:
            self.aircraft_intervals[ac["aircraft_id"]] = []
        for cr in crew:
            self.crew_intervals[cr["crew_id"]] = []

    def add_assignment_uniqueness_constraints(
        self,
        tasks: list[dict[str, Any]],
        aircraft: list[dict[str, Any]],
        crew: list[dict[str, Any]],
    ) -> None:
        """Ensure fulfilled tasks have exactly one aircraft and one crew assigned."""
        for t in tasks:
            tid = t["task_id"]
            # Sum of aircraft assignments must equal fulfillment variable u[tid]
            self.model.Add(
                sum(self.x[(tid, ac["aircraft_id"])] for ac in aircraft) == self.u[tid]
            )
            # Sum of crew assignments must equal fulfillment variable u[tid]
            self.model.Add(
                sum(self.y[(tid, cr["crew_id"])] for cr in crew) == self.u[tid]
            )

    def add_capability_and_qualification_constraints(
        self,
        tasks: list[dict[str, Any]],
        aircraft: list[dict[str, Any]],
        crew: list[dict[str, Any]],
    ) -> None:
        """Enforce aircraft capability matching and crew certification requirements."""
        for t in tasks:
            tid = t["task_id"]
            req_type = t.get("required_capability") or t.get("required_type")
            req_qual = t.get("required_qualification") or req_type

            # Aircraft capability matching
            for ac in aircraft:
                aid = ac["aircraft_id"]
                ac_cap = ac.get("capability_class") or ac.get("type_id")
                if req_type and ac_cap != req_type:
                    self.model.Add(self.x[(tid, aid)] == 0)

            # Crew qualification matching
            for cr in crew:
                cid = cr["crew_id"]
                cr_quals = cr.get("certified_classes") or [cr.get("qualification")]
                if req_qual and req_qual not in cr_quals:
                    self.model.Add(self.y[(tid, cid)] == 0)

    def add_aircraft_no_overlap_constraints(
        self,
        tasks: list[dict[str, Any]],
        aircraft: list[dict[str, Any]],
    ) -> None:
        """Ensure an airframe is never scheduled for overlapping sorties."""
        for ac in aircraft:
            aid = ac["aircraft_id"]
            turnaround = int(ac.get("nominal_turnaround_minutes", 60))

            for t in tasks:
                tid = t["task_id"]
                duration = int(t["duration_minutes"])
                total_interval = duration + turnaround

                # Optional interval present only if aircraft assigned to task
                interval_var = self.model.NewOptionalIntervalVar(
                    start=self.start_vars[tid],
                    size=total_interval,
                    end=self.end_vars[tid] + turnaround,
                    is_present=self.x[(tid, aid)],
                    name=f"interval_ac_{aid}_{tid}",
                )
                self.aircraft_intervals[aid].append(interval_var)

            # Disjunctive constraint: No two intervals on this aircraft can overlap
            self.model.AddNoOverlap(self.aircraft_intervals[aid])

    def add_crew_duty_and_rest_constraints(
        self,
        tasks: list[dict[str, Any]],
        crew: list[dict[str, Any]],
    ) -> None:
        """Enforce maximum continuous flight duty and minimum mandatory rest hours."""
        for cr in crew:
            cid = cr["crew_id"]
            max_duty = int(cr.get("max_duty_minutes_24h", 480))  # 8 hours default
            min_rest = int(cr.get("min_rest_minutes", 720))      # 12 hours default

            # Cumulative flight duration limit
            flight_minutes = [
                self.y[(t["task_id"], cid)] * int(t["duration_minutes"])
                for t in tasks
            ]
            self.model.Add(sum(flight_minutes) <= max_duty)

            # Mandatory rest intervals between consecutive duties
            for t in tasks:
                tid = t["task_id"]
                duration = int(t["duration_minutes"])
                total_duty_block = duration + min_rest

                interval_var = self.model.NewOptionalIntervalVar(
                    start=self.start_vars[tid],
                    size=total_duty_block,
                    end=self.end_vars[tid] + min_rest,
                    is_present=self.y[(tid, cid)],
                    name=f"interval_cr_{cid}_{tid}",
                )
                self.crew_intervals[cid].append(interval_var)

            # Disjunctive constraint: Crew duties with rest buffers cannot overlap
            self.model.AddNoOverlap(self.crew_intervals[cid])

    def add_runway_slot_capacity_constraints(
        self,
        tasks: list[dict[str, Any]],
        airbases: list[dict[str, Any]],
        planning_horizon_hours: int = 24,
    ) -> None:
        """Enforce hourly movement limits (takeoffs & landings) at each airbase."""
        for base in airbases:
            bid = base["airbase_id"]
            hourly_limit = int(base.get("max_hourly_movements", 20))

            for h in range(planning_horizon_hours):
                hour_start = h * 60
                hour_end = (h + 1) * 60

                movements_in_hour = []
                for t in tasks:
                    tid = t["task_id"]
                    origin = t.get("origin_base_id") or t.get("origin")
                    dest = t.get("dest_base_id") or t.get("dest")

                    # Departure movement at origin
                    if origin == bid:
                        dep_in_hour = self.model.NewBoolVar(f"dep_{tid}_{bid}_h{h}")
                        self.model.Add(self.start_vars[tid] >= hour_start).OnlyEnforceIf(dep_in_hour)
                        self.model.Add(self.start_vars[tid] < hour_end).OnlyEnforceIf(dep_in_hour)
                        # dep_in_hour implies task is fulfilled
                        self.model.AddImplication(dep_in_hour, self.u[tid])
                        movements_in_hour.append(dep_in_hour)

                    # Arrival movement at destination
                    if dest == bid:
                        arr_in_hour = self.model.NewBoolVar(f"arr_{tid}_{bid}_h{h}")
                        self.model.Add(self.end_vars[tid] >= hour_start).OnlyEnforceIf(arr_in_hour)
                        self.model.Add(self.end_vars[tid] < hour_end).OnlyEnforceIf(arr_in_hour)
                        self.model.AddImplication(arr_in_hour, self.u[tid])
                        movements_in_hour.append(arr_in_hour)

                if movements_in_hour:
                    self.model.Add(sum(movements_in_hour) <= hourly_limit)

    def add_maintenance_lockout_constraints(
        self,
        tasks: list[dict[str, Any]],
        maintenance_windows: list[dict[str, Any]],
    ) -> None:
        """Lock out aircraft undergoing scheduled maintenance inspections."""
        for mw in maintenance_windows:
            aid = mw["aircraft_id"]
            m_start = int(mw["start_minute"])
            m_end = int(mw["end_minute"])

            if aid in self.aircraft_intervals:
                # Add fixed maintenance window interval to aircraft interval list
                maint_interval = self.model.NewIntervalVar(
                    start=m_start,
                    size=m_end - m_start,
                    end=m_end,
                    name=f"maint_lockout_{aid}_{m_start}_{m_end}",
                )
                self.aircraft_intervals[aid].append(maint_interval)
