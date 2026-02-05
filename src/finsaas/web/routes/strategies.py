"""Strategy listing and parameter introspection endpoints."""

from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, HTTPException

from finsaas.strategy.parameters import (
    BoolParam,
    EnumParam,
    FloatParam,
    IntParam,
    ParamDescriptor,
)
from finsaas.strategy.registry import get_strategy, list_strategies
from finsaas.web.schemas import ParamInfo, StrategyInfo, StrategyParamsResponse

router = APIRouter(tags=["strategies"])


@router.get("/strategies")
def get_strategies() -> list[StrategyInfo]:
    return [StrategyInfo(name=name) for name in list_strategies()]


@router.get("/strategies/{name}/params")
def get_strategy_params(name: str) -> StrategyParamsResponse:
    try:
        cls = get_strategy(name)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

    descriptors: dict[str, ParamDescriptor] = getattr(cls, "_param_descriptors", {})
    params: list[ParamInfo] = []

    for attr_name, desc in descriptors.items():
        info = ParamInfo(
            name=attr_name,
            type=_param_type(desc),
            default=_to_json(desc.default),
            description=desc.description,
        )
        if isinstance(desc, IntParam):
            info.min_val = desc.min_val
            info.max_val = desc.max_val
            info.step = desc.step
        elif isinstance(desc, FloatParam):
            info.min_val = _to_json(desc.min_val)
            info.max_val = _to_json(desc.max_val)
            info.step = _to_json(desc.step)
        elif isinstance(desc, EnumParam):
            info.choices = [_to_json(c) for c in desc.choices]
        params.append(info)

    return StrategyParamsResponse(name=name, params=params)


def _param_type(desc: ParamDescriptor) -> str:
    if isinstance(desc, IntParam):
        return "int"
    if isinstance(desc, FloatParam):
        return "float"
    if isinstance(desc, BoolParam):
        return "bool"
    if isinstance(desc, EnumParam):
        return "enum"
    return "any"


def _to_json(val: object) -> object:
    if isinstance(val, Decimal):
        return float(val)
    return val
