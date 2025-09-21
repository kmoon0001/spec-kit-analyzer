import pytest
from unittest.mock import patch
from src import cli

def test_cli_main_runs():
    """
    Tests that the main function in the cli module runs without errors.
    """
    with patch('sys.argv', ['src/cli.py', 'ingest', '--dir', 'test_data']):
        with pytest.raises(SystemExit) as e:
            cli.main()
        assert e.type == SystemExit
        assert e.value.code == 0
