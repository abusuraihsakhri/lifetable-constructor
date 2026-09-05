import lifetable as m
import math


def test_smoke():
    r = m.assess_row({'value': 10})
    assert isinstance(r, dict)


def test_calculate_meld_na():
    # Normal values
    r = m.calculate_meld_na(bilirubin=1.0, creatinine=1.0, inr=1.0, sodium=137)
    assert "meld_na" in r
    assert r["severity"] == "low"

    # High values
    r = m.calculate_meld_na(bilirubin=10.0, creatinine=3.0, inr=2.5, sodium=125)
    assert r["meld_na"] >= 20
    assert r["severity"] in ("moderate", "high")

    # Dialysis case
    r = m.calculate_meld_na(bilirubin=2.0, creatinine=1.0, inr=1.2, dialysis=True)
    assert r["meld_na"] >= 6.0

    # Missing optional params
    r = m.calculate_meld_na(bilirubin=2.0, creatinine=1.2)
    assert "meld_na" in r


def test_calculate_qtc():
    # Normal QTc
    r = m.calculate_qtc(qt_ms=400, hr_bpm=60)
    assert "qtc_ms" in r
    assert r["risk"] == "normal"

    # Prolonged QTc
    r = m.calculate_qtc(qt_ms=500, hr_bpm=60)
    assert r["qtc_ms"] > 470
    assert r["risk"] in ("borderline", "high")

    # Using RR interval
    r = m.calculate_qtc(qt_ms=420, rr_ms=1000)
    assert "qtc_ms" in r

    # Invalid input
    r = m.calculate_qtc(qt_ms=-100)
    assert "error" in r


def test_calculate_bmi_z():
    # Adult normal BMI (use adult age to get adult reference)
    r = m.calculate_bmi_z(weight_kg=70, height_cm=175, age_months=240, sex="M")
    assert "bmi" in r
    assert "z_score" in r
    assert r["bmi"] == 22.86
    assert r["category"] == "normal"

    # Child (age_months <= 120 uses pediatric reference)
    r = m.calculate_bmi_z(weight_kg=20, height_cm=110, age_months=60)
    assert r["bmi"] > 0
    assert "z_score" in r

    # Obese category
    r = m.calculate_bmi_z(weight_kg=100, height_cm=175, age_months=240)
    assert r["category"] == "obese"

    # Invalid input
    r = m.calculate_bmi_z(weight_kg=-10, height_cm=0)
    assert "error" in r


def test_convert_hba1c():
    # HbA1c to eAG
    r = m.convert_hba1c(hba1c_percent=7.0)
    assert "eag_mgdl" in r
    assert "eag_mmol_l" in r
    assert abs(r["eag_mgdl"] - 154.2) < 1.0

    # eAG to HbA1c
    r = m.convert_hba1c(eag_mgdl=154.2)
    assert "hba1c_percent" in r
    assert abs(r["hba1c_percent"] - 7.0) < 0.2

    # No input
    r = m.convert_hba1c()
    assert "error" in r


def test_calculate_apri_fib4():
    # Normal values
    r = m.calculate_apri_fib4(ast_u_l=30, alt_u_l=30, platelets_109=250, age_years=40)
    assert "apri" in r
    assert "fib4" in r
    assert r["fibrosis_risk"] == "low"

    # High fibrosis risk
    r = m.calculate_apri_fib4(ast_u_l=120, alt_u_l=80, platelets_109=100, age_years=65)
    assert r["fib4"] > 3.25
    assert r["fibrosis_risk"] == "high"


def test_assess_row_routing():
    # MELD-Na routing
    r = m.assess_row({"bilirubin": 2.0, "creatinine": 1.2, "inr": 1.3})
    assert "meld_na" in r

    # QTc routing
    r = m.assess_row({"qt_ms": 420, "hr_bpm": 72})
    assert "qtc_ms" in r

    # BMI routing
    r = m.assess_row({"weight_kg": 70, "height_cm": 175})
    assert "bmi" in r

    # HbA1c routing
    r = m.assess_row({"hba1c_percent": 7.0})
    assert "eag_mgdl" in r

    # APRI routing
    r = m.assess_row({"ast_u_l": 50})
    assert "apri" in r

    # Fallback to generic score
    r = m.assess_row({"unknown_key": 42})
    assert "score" in r

    # Invalid input type
    r = m.assess_row("not a dict")
    assert "error" in r


def test_safe_float():
    assert m._safe_float(None) == 0.0
    assert m._safe_float("3.14") == 3.14
    assert m._safe_float(42) == 42.0
    assert m._safe_float("invalid", 1.0) == 1.0
    assert m._safe_float("-5") == -5.0


def test_validate_path_traversal():
    import pytest
    with pytest.raises(ValueError, match="Path traversal"):
        m._validate_path("../../etc/passwd")


def test_process_csv_path_validation():
    import pytest
    # Path traversal in input
    with pytest.raises(ValueError, match="Path traversal"):
        m.process_csv("../etc/passwd", "output.csv")
    # Path traversal in output (validated after input exists check)
    with pytest.raises((ValueError, FileNotFoundError)):
        m.process_csv("nonexistent_file.csv", "../etc/output.csv")
    # Missing input file
    with pytest.raises(FileNotFoundError):
        m.process_csv("nonexistent_file_xyz.csv", "output.csv")
