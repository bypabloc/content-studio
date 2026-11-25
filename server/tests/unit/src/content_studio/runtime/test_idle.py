"""Spec 028, AC-5: el server se apaga tras api.idle_minutes sin uso, pero no con trabajos en cola o corriendo."""

from content_studio.runtime import idle


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def test_ac5_exits_when_idle_but_not_with_jobs():
    clock = FakeClock()
    clock_idle = idle.IdleClock(minutes=1, clock=clock)
    assert clock_idle.idle(busy=False) is False
    clock.now = 61
    assert clock_idle.idle(busy=False) is True
    assert clock_idle.idle(busy=True) is False
    clock_idle.touch()
    assert clock_idle.idle(busy=False) is False
