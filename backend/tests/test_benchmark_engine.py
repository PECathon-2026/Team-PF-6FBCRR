import pytest
from app.services.benchmark_engine import benchmark_engine
from app.models.schemas import BenchmarkPolicy


@pytest.mark.asyncio
async def test_adversarial_benchmark_execution():
    result = await benchmark_engine.run_benchmark()
    assert result.run_id.startswith("bench_run_")
    assert len(result.comparisons) == 3

    # Extract results by policy
    by_policy = {c.policy: c for c in result.comparisons}

    unprotected = by_policy[BenchmarkPolicy.UNPROTECTED_BASELINE]
    basic = by_policy[BenchmarkPolicy.BASIC_REDACTION]
    privacylens = by_policy[BenchmarkPolicy.PRIVACYLENS_TASK_SCOPED]

    # Invariants for benchmark:
    # 1. Unprotected baseline leaks 100% of sensitive items
    assert unprotected.unauthorized_disclosure_rate == 100.0

    # 2. Basic redaction leaks more than PrivacyLens (e.g. misses canaries and tokens)
    assert basic.unauthorized_disclosure_rate > privacylens.unauthorized_disclosure_rate

    # 3. PrivacyLens achieves zero unauthorized disclosure
    assert privacylens.unauthorized_disclosure_rate == 0.0

    # 4. PrivacyLens preserves high task utility
    assert privacylens.useful_context_retained_score >= 90.0

    assert "PrivacyLens Task-Scoped Enforcement achieved 0.0% unauthorized disclosure" in result.summary_conclusion
