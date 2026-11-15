import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from streamlit.testing.v1 import AppTest


def test_app_runs_and_generates_plans():
    at = AppTest.from_file(str(pathlib.Path(__file__).parent.parent / "app.py"), default_timeout=120).run()
    assert not at.exception, at.exception
    btn = next(b for b in at.button if "Generate" in b.label)
    btn.click().run()
    assert not at.exception, at.exception
    assert len(at.dataframe) >= 1
