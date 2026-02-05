"""Optimization execution endpoint."""

from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, HTTPException

from finsaas.web import UPLOAD_DIR
from finsaas.web.schemas import OptimizeRequest, OptimizeResponse, TrialResponse

router = APIRouter(tags=["optimize"])


@router.post("/optimize")
def run_optimize(req: OptimizeRequest) -> OptimizeResponse:
    from finsaas.api.facade import optimize
    from finsaas.strategy.registry import get_strategy

    csv_path = UPLOAD_DIR / req.csv_file
    if not csv_path.exists():
        raise HTTPException(status_code=404, detail=f"CSV file not found: {req.csv_file}")

    try:
        cls = get_strategy(req.strategy)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

    try:
        result = optimize(
            strategy_cls=cls,
            csv_path=str(csv_path),
            symbol=req.symbol,
            timeframe=req.timeframe,
            initial_capital=Decimal(str(req.initial_capital)),
            method=req.method,
            objective=req.objective,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    trials = [
        TrialResponse(
            trial_index=t.trial_index,
            parameters={k: _to_json(v) for k, v in t.parameters.items()},
            objective_value=float(t.objective_value),
            metrics={k: float(v) for k, v in t.metrics.items()},
        )
        for t in result.all_trials
    ]

    return OptimizeResponse(
        method=result.method,
        objective=result.objective_name,
        total_trials=result.total_trials,
        best_params={k: _to_json(v) for k, v in result.best_params.items()},
        best_value=float(result.best_value),
        trials=trials,
    )


def _to_json(val: object) -> object:
    if isinstance(val, Decimal):
        return float(val)
    return val
