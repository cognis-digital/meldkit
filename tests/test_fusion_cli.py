import json

from obsidia import cli


def test_demo_fusion_runs(capsys):
    assert cli.main(["demo-fusion"]) == 0
    out = capsys.readouterr().out
    assert "Common Operating Picture" in out
    assert "STIX bundle" in out


def test_fuse_writes_html(tmp_path, capsys):
    html = tmp_path / "cop.html"
    assert cli.main(["fuse", "--html", str(html)]) == 0
    assert html.exists()
    content = html.read_text(encoding="utf-8")
    assert content.startswith("<!doctype html>")


def test_dossier_json_output(capsys):
    assert cli.main(["dossier", "--entity", "Nightjar"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data and "Nightjar" in data[0]["entity"]["canonical"]


def test_dossier_no_match(capsys):
    assert cli.main(["dossier", "--entity", "zzz-nope"]) == 1


def test_export_stix(capsys):
    assert cli.main(["export", "--format", "stix"]) == 0
    b = json.loads(capsys.readouterr().out)
    assert b["type"] == "bundle"


def test_export_csv(capsys):
    assert cli.main(["export", "--format", "csv"]) == 0
    out = capsys.readouterr().out
    assert "discipline" in out.splitlines()[0]


def test_export_symbols_no_symbol_codes(capsys):
    assert cli.main(["export", "--format", "symbols"]) == 0
    out = capsys.readouterr().out.lower()
    assert "2525" not in out and "app-6" not in out


def test_export_to_file(tmp_path, capsys):
    out = tmp_path / "x.json"
    assert cli.main(["export", "--format", "json", "--out", str(out)]) == 0
    assert out.exists()


def test_fuse_default_scenario(capsys):
    assert cli.main(["fuse"]) == 0
    assert "observations" in capsys.readouterr().out.lower()
