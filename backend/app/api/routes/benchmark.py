from fastapi import APIRouter
from typing import List
from app.models.schemas import (
    BenchmarkRunResponse,
    BenchmarkTaskSpec,
)
from app.services.benchmark_engine import benchmark_engine
from app.services.task_manager import task_manager

router = APIRouter(prefix="/benchmark", tags=["Privacy Policy Lab & Adversarial Benchmark"])


@router.post("/run", response_model=BenchmarkRunResponse)
async def run_adversarial_benchmark():
    """
    Executes the repeatable adversarial benchmark comparing:
    1. UNPROTECTED_BASELINE
    2. BASIC_REDACTION
    3. PRIVACYLENS_TASK_SCOPED
    Computes unauthorized disclosure rate, detection precision/recall,
    task success, false blocking rate, and context utility.
    """
    response = await benchmark_engine.run_benchmark()
    task_manager.record_benchmark_run(response)
    return response


@router.get("/history", response_model=List[BenchmarkRunResponse])
async def list_benchmark_history():
    """Returns historical benchmark run results."""
    return task_manager.get_benchmark_runs()


@router.get("/dataset", response_model=List[BenchmarkTaskSpec])
async def get_benchmark_dataset():
    """Inspects the 10 standardized synthetic adversarial tasks and test specs."""
    return benchmark_engine.get_benchmark_dataset()
