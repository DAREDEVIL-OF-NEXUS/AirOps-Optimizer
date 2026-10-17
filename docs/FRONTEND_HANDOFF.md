# AIRWISE Frontend Handoff Specification & API Interface Contracts

**Author:** Lakshay Bharti (Senior OR Engineer & ML Architect)  
**Audience:** Frontend Development Team, System Integrators  
**Version:** 1.0.0 (Frozen Interface)  
**Status:** APPROVED & CODE-ALIGNED  

---

## 1. Overview & Architecture Boundary

The core engineering workstream (Lakshay Bharti) delivers the mathematical optimization solvers, predictive machine learning models, and disruption risk profiling services. The frontend team communicates with this engine via RESTful / JSON RPC interfaces.

This document establishes the frozen schemas, status codes, and TypeScript typings so the frontend dashboard can render flight allocations, schedule timelines, resource bottlenecks, and counterfactual comparisons.

---

## 2. Core Endpoint Specifications

### 2.1 `POST /api/v1/optimize`
Solves the dynamic resource allocation problem for a given operational state.

#### Request Payload: `OptimizeRequest`
```json
{
  "state": {
    "tasks": [
      {
        "task_id": "MISSION-001",
        "earliest_start_minute": 60,
        "latest_start_minute": 120,
        "duration_minutes": 90,
        "priority": 5.0,
        "required_capability": "FAST_JET",
        "required_qualification": "NIGHT_VISION"
      }
    ],
    "aircraft": [
      {
        "aircraft_id": "SU30-01",
        "capability_class": "FAST_JET",
        "nominal_turnaround_minutes": 45,
        "flight_hours": 1250.5,
        "total_cycles": 620
      }
    ],
    "crew": [
      {
        "crew_id": "PILOT-ALPHA",
        "certified_classes": ["FAST_JET"],
        "max_duty_minutes_24h": 480,
        "min_rest_minutes": 720
      }
    ],
    "airbases": [
      {
        "airbase_id": "BASE-NORTH",
        "max_hourly_movements": 10
      }
    ],
    "maintenance_windows": [
      {
        "aircraft_id": "SU30-01",
        "start_minute": 600,
        "end_minute": 720
      }
    ]
  },
  "config": {
    "solver_type": "OR_TOOLS_CP_SAT",
    "time_limit_seconds": 30.0,
    "weight_priority": 1000,
    "weight_delay_minute": 10,
    "weight_risk": 500,
    "weight_churn": 250
  },
  "risk_aware": true
}
```

#### Response Envelope: `OptimizeResponse`
```json
{
  "status": "OPTIMAL",
  "objective_value": 49850.0,
  "best_bound": 49850.0,
  "optimality_gap": 0.0,
  "runtime_seconds": 0.042,
  "solver_name": "RiskAware-CPSAT",
  "assignments": [
    {
      "task_id": "MISSION-001",
      "aircraft_id": "SU30-01",
      "crew_id": "PILOT-ALPHA",
      "scheduled_start_minute": 60,
      "scheduled_end_minute": 150,
      "delay_minutes": 0,
      "turnaround_buffer_minutes": 45,
      "duration_minutes": 90,
      "metadata": {}
    }
  ],
  "unassigned_task_ids": [],
  "infeasibility_reasons": [],
  "diagnostic_metrics": {
    "predictive_intelligence": {
      "evaluated_risk_assets": 1,
      "dynamic_delays_applied": 1,
      "inference_latency_ms": 1.42
    }
  }
}
```

---

### 2.2 `POST /api/v1/predict/risks`
Evaluates 24-hour component failure probabilities and expected turnaround delays.

#### Request Payload: `PredictRiskRequest`
```json
{
  "state": { ... },
  "cutoff_minute": 0.0,
  "horizon_hours": 24.0
}
```

#### Response Envelope: `PredictRiskResponse`
```json
{
  "aircraft_failure_probabilities": {
    "SU30-01": 0.042,
    "MIG29-02": 0.815
  },
  "task_turnaround_delays": {
    "MISSION-001": 12.5
  },
  "inference_latency_ms": 2.14,
  "metadata": {
    "evaluated_aircraft_count": 2,
    "evaluated_task_count": 1
  }
}
```

---

### 2.3 `POST /api/v1/diagnose/infeasibility`
Returns plain-English explanations and recommended schedule relaxations when missions cannot be scheduled.

#### Response Envelope: `InfeasibilityReport`
```json
{
  "is_feasible": false,
  "unassigned_task_count": 1,
  "unassigned_task_ids": ["MISSION-999"],
  "bottlenecks": [
    {
      "category": "CREW_DUTY_LIMIT",
      "resource_id": "CREW_DUTY_LIMIT",
      "affected_task_ids": ["MISSION-999"],
      "description": "Task 'MISSION-999' requires duration 540m, exceeding the maximum allowable 24h duty ceiling of all qualified crew.",
      "recommended_relaxation": "Grant duty-time extension waiver or divide task into multi-leg sorties.",
      "severity": "HIGH"
    }
  ],
  "explanations": [
    "Task 'MISSION-999' requires duration 540m, exceeding the maximum allowable 24h duty ceiling of all qualified crew."
  ],
  "recommended_actions": [
    "Crew fatigue management: Stage auxiliary relief crews for long-duration sorties."
  ]
}
```

---

## 3. TypeScript Interfaces for Frontend Engineers

```typescript
// types/airops-contracts.ts

export type SolverStatus = 
  | "OPTIMAL" 
  | "FEASIBLE" 
  | "INFEASIBLE" 
  | "MODEL_INVALID" 
  | "UNKNOWN";

export type BottleneckSeverity = "CRITICAL" | "HIGH" | "MEDIUM";

export type BottleneckCategory =
  | "AIRCRAFT_CAPABILITY"
  | "CREW_QUALIFICATION"
  | "CREW_DUTY_LIMIT"
  | "RUNWAY_CAPACITY"
  | "MAINTENANCE_LOCKOUT"
  | "FLEET_SATURATION";

export interface TaskAssignment {
  task_id: string;
  aircraft_id: string;
  crew_id: string;
  scheduled_start_minute: number;
  scheduled_end_minute: number;
  delay_minutes: number;
  turnaround_buffer_minutes: number;
  duration_minutes: number;
  metadata?: Record<string, unknown>;
}

export interface DiagnosticBottleneck {
  category: BottleneckCategory;
  resource_id: string;
  affected_task_ids: string[];
  description: string;
  recommended_relaxation: string;
  severity: BottleneckSeverity;
}

export interface OptimizationResult {
  status: SolverStatus;
  objective_value: number;
  best_bound: number;
  optimality_gap: number;
  runtime_seconds: number;
  assignments: TaskAssignment[];
  unassigned_task_ids: string[];
  infeasibility_reasons: string[];
  solver_name: string;
  diagnostic_metrics: Record<string, unknown>;
}

export interface DisruptionRiskProfile {
  aircraft_failure_probabilities: Record<string, number>;
  task_turnaround_delays: Record<string, number>;
  inference_latency_ms: number;
  metadata?: Record<string, unknown>;
}
```

---

## 4. Error Code Conventions

| HTTP Status | Error Code | Description | UI Action |
| :--- | :--- | :--- | :--- |
| `200 OK` | `SUCCESS` | Optimization or prediction completed normally. | Render Gantt chart and asset status. |
| `422 Unprocessable` | `INVALID_PAYLOAD` | Missing required fields, inverted time bounds. | Display inline validation badge. |
| `504 Gateway Timeout` | `SOLVER_TIMEOUT` | Hard constraint search exceeded timeout limit. | Present partial primal solution or relax constraints. |
