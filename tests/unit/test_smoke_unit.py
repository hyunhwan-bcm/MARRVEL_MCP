import pytest


def test_version_is_string():
    """Simple unit smoke test to ensure package importable and version is set.

    This test is intentionally minimal and does not require network or heavy
    dependencies. It ensures CI runs at least one unit test when filtering with
    `-m "not integration"` so coverage data is collected.
    """
    import src

    assert isinstance(src.__version__, str)
