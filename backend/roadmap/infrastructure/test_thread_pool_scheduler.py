"""ThreadPoolJobScheduler のテスト。"""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from uuid import UUID, uuid4

import pytest


class _RecordingJobRunner:
    """ジョブ実行を記録するテストダブル。"""

    def __init__(self) -> None:
        self.calls: list[tuple[UUID, str]] = []
        self.thread_ids: list[int] = []
        self._lock = threading.Lock()
        self._event = threading.Event()
        self._expected_count = 1

    def expect(self, count: int) -> None:
        self._expected_count = count
        self._event.clear()

    def __call__(self, job_id: UUID, topic: str) -> None:
        with self._lock:
            self.calls.append((job_id, topic))
            self.thread_ids.append(threading.current_thread().ident or 0)
            if len(self.calls) >= self._expected_count:
                self._event.set()

    def wait(self, timeout: float = 5.0) -> bool:
        return self._event.wait(timeout)


class _BlockingJobRunner:
    """enqueue が非同期であることを検証するためのブロッキング runner。"""

    def __init__(self) -> None:
        self.started = threading.Event()
        self.release = threading.Event()

    def __call__(self, job_id: UUID, topic: str) -> None:
        self.started.set()
        if not self.release.wait(timeout=30.0):
            msg = "BlockingJobRunner was never released"
            raise TimeoutError(msg)


class TestThreadPoolJobScheduler:
    def test_enqueue_returns_before_runner_completes(self) -> None:
        from roadmap.infrastructure.thread_pool_scheduler import (
            ThreadPoolJobScheduler,
        )

        blocker = _BlockingJobRunner()
        with ThreadPoolExecutor(max_workers=1) as executor:
            scheduler = ThreadPoolJobScheduler(executor=executor, job_runner=blocker)

            scheduler.enqueue_roadmap_generation(uuid4(), "TypeScript")
            # enqueue returned but runner is still blocked on release
            assert not blocker.release.is_set()
            assert blocker.started.wait(timeout=5.0)
            blocker.release.set()

    def test_enqueue_runs_job_on_different_thread(self) -> None:
        from roadmap.infrastructure.thread_pool_scheduler import (
            ThreadPoolJobScheduler,
        )

        runner = _RecordingJobRunner()
        caller_thread_id = threading.current_thread().ident
        with ThreadPoolExecutor(max_workers=1) as executor:
            scheduler = ThreadPoolJobScheduler(executor=executor, job_runner=runner)

            scheduler.enqueue_roadmap_generation(uuid4(), "TypeScript")

            assert runner.wait(timeout=5.0)
            assert len(runner.calls) == 1
            assert runner.thread_ids[0] != caller_thread_id

    def test_enqueue_submits_job_with_correct_args(self) -> None:
        from roadmap.infrastructure.thread_pool_scheduler import (
            ThreadPoolJobScheduler,
        )

        runner = _RecordingJobRunner()
        with ThreadPoolExecutor(max_workers=1) as executor:
            scheduler = ThreadPoolJobScheduler(executor=executor, job_runner=runner)
            job_id = uuid4()

            scheduler.enqueue_roadmap_generation(job_id, "TypeScript")

            assert runner.wait(timeout=5.0)
            assert runner.calls == [(job_id, "TypeScript")]

    def test_enqueue_raises_schedule_error_on_submission_failure(self) -> None:
        from roadmap.domain.roadmap_generation_types import (
            RoadmapGenerationScheduleError,
        )
        from roadmap.infrastructure.thread_pool_scheduler import (
            ThreadPoolJobScheduler,
        )

        runner = _RecordingJobRunner()
        executor = ThreadPoolExecutor(max_workers=1)
        executor.shutdown(wait=False)
        scheduler = ThreadPoolJobScheduler(executor=executor, job_runner=runner)

        with pytest.raises(RoadmapGenerationScheduleError) as exc_info:
            scheduler.enqueue_roadmap_generation(uuid4(), "TypeScript")

        assert runner.calls == []
        cause = exc_info.value.__cause__
        assert cause is not None
        assert isinstance(cause, RuntimeError)

    def test_enqueue_multiple_jobs(self) -> None:
        from roadmap.infrastructure.thread_pool_scheduler import (
            ThreadPoolJobScheduler,
        )

        runner = _RecordingJobRunner()
        runner.expect(2)
        with ThreadPoolExecutor(max_workers=2) as executor:
            scheduler = ThreadPoolJobScheduler(executor=executor, job_runner=runner)
            id1, id2 = uuid4(), uuid4()

            scheduler.enqueue_roadmap_generation(id1, "React")
            scheduler.enqueue_roadmap_generation(id2, "Go")

            assert runner.wait(timeout=5.0)

        assert len(runner.calls) == 2
        submitted = {(c[0], c[1]) for c in runner.calls}
        assert submitted == {(id1, "React"), (id2, "Go")}

    def test_job_runner_exception_does_not_prevent_next_enqueue(self) -> None:
        from roadmap.infrastructure.thread_pool_scheduler import (
            ThreadPoolJobScheduler,
        )

        error_event = threading.Event()
        success_runner = _RecordingJobRunner()

        def failing_then_success(job_id: UUID, topic: str) -> None:
            if topic == "fail":
                error_event.set()
                msg = "intentional failure"
                raise RuntimeError(msg)
            success_runner(job_id, topic)

        with ThreadPoolExecutor(max_workers=1) as executor:
            scheduler = ThreadPoolJobScheduler(
                executor=executor,
                job_runner=failing_then_success,
            )

            scheduler.enqueue_roadmap_generation(uuid4(), "fail")
            assert error_event.wait(timeout=5.0)

            good_id = uuid4()
            scheduler.enqueue_roadmap_generation(good_id, "React")

            assert success_runner.wait(timeout=5.0)
            assert success_runner.calls[0] == (good_id, "React")
