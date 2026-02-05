"""Pydantic request/response models for the web API."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class BacktestRequest(BaseModel):
    strategy: str
    csv_file: str
    symbol: str = "UNKNOWN"
    timeframe: str = "1h"
    initial_capital: float = 10000.0
    commission: float = 0.001
    slippage: float = 0.0005
    parameters: Dict[str, Any] = {}


class TradeResponse(BaseModel):
    entry_time: str
    exit_time: str
    side: str
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float
    pnl_pct: float
    commission: float
    bars_held: int


class EquityPointResponse(BaseModel):
    bar_index: int
    timestamp: str
    equity: float
    cash: float
    position_value: float
    drawdown: float


class BacktestResponse(BaseModel):
    strategy: str
    run_hash: str
    parameters: Dict[str, str]
    config: Dict[str, Any]
    metrics: Dict[str, float]
    total_bars: int
    final_equity: float
    total_trades: int
    trades: List[TradeResponse]
    equity_curve: List[EquityPointResponse]


class StrategyInfo(BaseModel):
    name: str


class ParamInfo(BaseModel):
    name: str
    type: str
    default: Any
    description: str = ""
    min_val: Any = None
    max_val: Any = None
    step: Any = None
    choices: Optional[List[Any]] = None


class StrategyParamsResponse(BaseModel):
    name: str
    params: List[ParamInfo]


class FileInfo(BaseModel):
    name: str
    size: int
    bars: Optional[int] = None


class OptimizeRequest(BaseModel):
    strategy: str
    csv_file: str
    symbol: str = "UNKNOWN"
    timeframe: str = "1h"
    initial_capital: float = 10000.0
    method: str = "grid"
    objective: str = "sharpe"
    parameters: Dict[str, Any] = {}


class TrialResponse(BaseModel):
    trial_index: int
    parameters: Dict[str, Any]
    objective_value: float
    metrics: Dict[str, float]


class OptimizeResponse(BaseModel):
    method: str
    objective: str
    total_trials: int
    best_params: Dict[str, Any]
    best_value: float
    trials: List[TrialResponse]
