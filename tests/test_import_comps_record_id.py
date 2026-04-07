from scripts.import_comps import parse_row


def test_parse_row_uses_source_row_id_for_unique_record_id() -> None:
    base = {
        "postal_code": "75011",
        "lat": "48.86",
        "lon": "2.37",
        "price_eur": "350000",
        "sold_at": "2024-01-15",
        "transaction_id": "MUT-123",
        "property_type": "Appartement",
    }

    row1 = parse_row({**base, "source_row_id": "line-1"}, "dvf_2024.csv")
    row2 = parse_row({**base, "source_row_id": "line-1"}, "dvf_2025.csv")

    assert row1 is not None
    assert row2 is not None
    assert row1.transaction_id == row2.transaction_id
    assert row1.source == "dvf:dvf_2024.csv"
    assert row2.source == "dvf:dvf_2025.csv"
    assert row1.record_id != row2.record_id
