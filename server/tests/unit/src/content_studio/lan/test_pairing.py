"""Spec 032, AC-3: PIN de 6 dígitos, de un uso, que vence a los 5 min y se anula tras 5 intentos fallidos."""

from __future__ import annotations

import pytest

from content_studio.lan.pairing import MAX_FAILURES, TTL_S, Pairing, PairingError


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def _code(pairing: Pairing, pin: str) -> tuple[str, int]:
    with pytest.raises(PairingError) as caught:
        pairing.redeem(pin)
    return caught.value.code, caught.value.status


def test_ac3_pin_single_use_expires_and_locks():
    clock = FakeClock()
    pairing = Pairing(clock=clock)

    pin = pairing.new()['pin']
    pairing.redeem(pin)
    assert _code(pairing, pin) == ('pairing_invalid', 401)

    pin = pairing.new()['pin']
    clock.now += TTL_S
    assert _code(pairing, pin) == ('pairing_invalid', 401)

    pin = pairing.new()['pin']
    wrong = '000000' if pin != '000000' else '111111'
    for _ in range(MAX_FAILURES - 1):
        assert _code(pairing, wrong) == ('pairing_invalid', 401)
    assert _code(pairing, wrong) == ('pairing_locked', 429)
    assert _code(pairing, pin) == ('pairing_locked', 429)


def test_a_new_pin_has_six_digits_and_its_lifetime():
    pairing = Pairing(clock=FakeClock())

    created = pairing.new()

    assert len(created['pin']) == 6
    assert created['pin'].isdigit()
    assert created['expires_in'] == TTL_S


def test_without_a_pin_nothing_pairs():
    assert _code(Pairing(clock=FakeClock()), '123456') == ('pairing_invalid', 401)


def test_a_new_pin_clears_the_lock():
    pairing = Pairing(clock=FakeClock())
    pairing.new()
    for _ in range(MAX_FAILURES):
        _code(pairing, 'abcdef')

    pin = pairing.new()['pin']

    pairing.redeem(pin)


def test_a_non_ascii_pin_is_just_invalid():
    pairing = Pairing(clock=FakeClock())
    pairing.new()

    assert _code(pairing, 'ñññññ') == ('pairing_invalid', 401)
