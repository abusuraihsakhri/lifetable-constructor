"""Deterministic checks of the abridged life-table method."""
import csv
import pytest
from life_table import construct_life_table, read_intervals, write_table


def test_constant_mortality_hazard():
    table = construct_life_table([{"age": 0, "mx": 0.02}, {"age": 5, "mx": 0.02}])
    assert table[0]["qx"] == pytest.approx(5 * 0.02 / (1 + 2.5 * 0.02))
    assert table[0]["lx"] == 100_000
    assert table[-1]["qx"] == 1
    assert table[0]["ex"] == pytest.approx(50.0)
    assert sum(r["dx"] for r in table) == pytest.approx(100_000)
    assert table[0]["Tx"] == pytest.approx(sum(r["Lx"] for r in table))


def test_custom_ax_changes_person_years():
    baseline = construct_life_table([{"age": 0, "mx": .1}, {"age": 1, "mx": .01}])
    custom = construct_life_table([{"age": 0, "mx": .1, "ax": .1}, {"age": 1, "mx": .01}])
    assert custom[0]["ax"] == .1
    assert custom[0]["ex"] != baseline[0]["ex"]


def test_zero_mortality_and_cohort_exhaustion():
    table = construct_life_table([{"age": 0, "mx": 0}, {"age": 20, "mx": 0.1}])
    assert table[0]["qx"] == 0
    assert table[0]["lx"] == table[1]["lx"]
    assert table[0]["ex"] == pytest.approx(30)
    table = construct_life_table([{"age": 0, "mx": 10}, {"age": 1, "mx": .1}])
    assert table[0]["qx"] == 1
    assert table[1]["lx"] == 0
    assert table[1]["ex"] is None


@pytest.mark.parametrize("rows", [[], [{"age": 0, "mx": 0}], [{"age": -1, "mx": .1}],
    [{"age": 0, "mx": .1}, {"age": 0, "mx": .1}],
    [{"age": 0, "mx": -1}, {"age": 1, "mx": 1}],
    [{"age": 0, "mx": .1, "ax": 2}, {"age": 1, "mx": .1}],
    [{"age": 0, "mx": "NaN"}, {"age": 1, "mx": .1}],
    [{"age": 0, "mx": .1, "ax": .2}, {"age": 1, "mx": .1, "ax": .1}]])
def test_invalid_intervals(rows):
    with pytest.raises(ValueError):
        construct_life_table(rows)


def test_csv_round_trip(tmp_path):
    source = tmp_path / "source.csv"
    source.write_text("age,mx,ax\n0,0.02,\n5,0.02,\n")
    table = construct_life_table(read_intervals(source))
    dest = tmp_path / "output.csv"
    write_table(dest, table)
    with dest.open() as stream:
        actual = list(csv.DictReader(stream))
    assert len(actual) == 2
    assert float(actual[0]["ex"]) == pytest.approx(50.0)
    assert actual[1]["width"] == ""
