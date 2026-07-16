"""Tests for the UML-vs-code member-count balance calculator."""

from classpy.domain.balance import BalanceCalculator, SortMode
from classpy.domain.models import CodeClass, MemberKind, UmlClass, UmlMember


def _uml(name, *member_names):
    return UmlClass(
        name=name,
        package="",
        stereotype="planned",
        members=[UmlMember(n, MemberKind.METHOD) for n in member_names],
    )


def _code(name, methods=(), attributes=()):
    return CodeClass(
        name=name,
        module_path=f"src/{name.lower()}.py",
        methods=set(methods),
        attributes=set(attributes),
    )


def _by_name(entries):
    return {e.name: e for e in entries}


def test_diff_is_uml_minus_code():
    pairs = [(_uml("A", "x", "y", "z"), _code("A", methods=("x",)))]
    entry = BalanceCalculator().calculate(pairs)[0]
    assert entry.uml_count == 3
    assert entry.code_count == 1
    assert entry.diff == 2


def test_missing_code_class_counts_as_zero():
    entry = BalanceCalculator().calculate([(_uml("A", "x"), None)])[0]
    assert entry.code_count == 0
    assert entry.diff == 1


def test_private_members_excluded_by_default():
    pairs = [(_uml("A"), _code("A", methods=("run", "_helper", "__init__")))]
    entry = BalanceCalculator().calculate(pairs)[0]
    assert entry.code_count == 1  # only "run"
    assert entry.diff == -1


def test_private_members_counted_when_requested():
    pairs = [(_uml("A"), _code("A", methods=("run", "_helper", "__init__")))]
    entry = BalanceCalculator().calculate(pairs, count_private=True)[0]
    assert entry.code_count == 3


def test_private_toggle_does_not_touch_uml_side():
    # An underscore-named UML member still counts regardless of the flag.
    pairs = [(_uml("A", "_secret", "run"), _code("A"))]
    entry = BalanceCalculator().calculate(pairs, count_private=False)[0]
    assert entry.uml_count == 2


def test_sort_abs_puts_biggest_gap_first():
    pairs = [
        (_uml("Small", "a"), _code("Small")),  # diff +1
        (_uml("Big", "a", "b", "c", "d"), _code("Big")),  # diff +4
        (_uml("Mid", "a", "b"), _code("Mid")),  # diff +2
    ]
    names = [e.name for e in BalanceCalculator().calculate(pairs, sort=SortMode.ABS)]
    assert names == ["Big", "Mid", "Small"]


def test_sort_abs_treats_direction_symmetrically():
    pairs = [
        (_uml("Under"), _code("Under", methods=("a", "b", "c"))),  # diff -3
        (_uml("Over", "a"), _code("Over")),  # diff +1
    ]
    names = [e.name for e in BalanceCalculator().calculate(pairs, sort=SortMode.ABS)]
    assert names == ["Under", "Over"]  # |−3| > |+1|


def test_sort_signed_groups_uml_heavy_then_even_then_code_heavy():
    pairs = [
        (_uml("CodeHeavy"), _code("CodeHeavy", methods=("a", "b"))),  # -2
        (_uml("Even", "a"), _code("Even", methods=("a",))),  # 0
        (_uml("UmlHeavy", "a", "b", "c"), _code("UmlHeavy")),  # +3
    ]
    names = [
        e.name for e in BalanceCalculator().calculate(pairs, sort=SortMode.SIGNED)
    ]
    assert names == ["UmlHeavy", "Even", "CodeHeavy"]
