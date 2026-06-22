"""Tests for verification number/keyboard generation (pure logic)."""

from bot.handlers.verification import (
    generate_verification_keyboard,
    generate_verification_numbers,
)


def test_random_numbers_are_five_unique_digits():
    for _ in range(200):
        correct, numbers = generate_verification_numbers()
        assert len(numbers) == 5
        assert len(set(numbers)) == 5
        assert correct in numbers
        assert all(0 <= n <= 9 for n in numbers)


def test_fixed_correct_number_is_present():
    for target in range(10):
        correct, numbers = generate_verification_numbers(correct_number=target)
        assert correct == target
        assert target in numbers
        assert len(numbers) == 5
        assert len(set(numbers)) == 5


def test_keyboard_layout_is_three_then_two():
    kb = generate_verification_keyboard([1, 2, 3, 4, 5])
    rows = kb.inline_keyboard
    assert len(rows) == 2
    assert len(rows[0]) == 3
    assert len(rows[1]) == 2


def test_keyboard_callback_data():
    kb = generate_verification_keyboard([7, 8, 9, 0, 1])
    flat = [btn for row in kb.inline_keyboard for btn in row]
    assert [b.text for b in flat] == ["7", "8", "9", "0", "1"]
    assert [b.callback_data for b in flat] == [
        "verify:7",
        "verify:8",
        "verify:9",
        "verify:0",
        "verify:1",
    ]
