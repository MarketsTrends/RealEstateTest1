from app.db.comps_repo import build_comps_filters
from app.schemas import PropertyType


def test_build_comps_filters_unknown_without_surface() -> None:
    clause, params = build_comps_filters(
        property_type=PropertyType.unknown,
        surface_m2=None,
        surface_tolerance_pct=0.2,
    )
    assert clause == ""
    assert params == {}


def test_build_comps_filters_with_type_and_surface() -> None:
    clause, params = build_comps_filters(
        property_type=PropertyType.apartment,
        surface_m2=50,
        surface_tolerance_pct=0.2,
    )
    assert "property_type" in clause
    assert "surface_m2 BETWEEN" in clause
    assert params["property_type"] == "apartment"
    assert params["surface_min"] == 40
    assert params["surface_max"] == 60
