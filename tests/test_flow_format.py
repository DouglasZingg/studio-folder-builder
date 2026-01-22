from builder.integrations.flow_client import format_seq_shots_text


def test_format_seq_shots_text():
    data = {"SQ020": ["SH020"], "SQ010": ["SH010", "SH020"]}
    out = format_seq_shots_text(data)
    assert "SQ010:" in out
    assert "SQ020:" in out
    assert out.splitlines()[0].startswith("SQ010:")
