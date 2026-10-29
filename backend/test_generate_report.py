def test_import_has_no_side_effects():
    import backend.generate_report  # must not read or write files on import