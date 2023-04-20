
import IPython.testing.globalipapp as testing
import IPython.core.error as error

import pytest
import unittest.mock as mock

import snakeviz.ipymagic


@pytest.fixture(scope="module")
def shell():
    result = testing.get_ipython()
    result.run_line_magic("load_ext", "snakeviz")
    return result

def test_snakeviz_magic_browser_default(shell):
    # Since we use the test shell we need to make sure we try to embed the display by
    # faking that we have an interactive shell:
    with mock.patch.object(snakeviz.ipymagic, "_check_ipynb", return_value=True):

        with mock.patch.object(snakeviz.ipymagic, "display") as mock_display:
            shell.run_line_magic("snakeviz", "print()")
            assert mock_display.called
            html = mock_display.call_args[0][0]._repr_html_()
            assert "\" + document.location.hostname + \"" in html


@pytest.mark.parametrize("config_str,test_str",
    (
        ("-h localhost", "localhost"),
        ("-p 8900", "8900"),
         ("--host=localhost", "localhost"),
         ("--port=8900", "8900"),
         ("-h localhost -p 8900", "localhost:8900"),
    )
)
def test_snakeviz_config(config_str, test_str, shell):
    shell.run_line_magic("snakeviz_config", config_str)
    # Since we use the test shell we need to make sure we try to embed the display by
    # faking that we have an interactive shell:
    with mock.patch.object(snakeviz.ipymagic, "_check_ipynb", return_value=True):
        with mock.patch.object(snakeviz.ipymagic, "display") as mock_display:
            shell.run_line_magic("snakeviz", "print()")
            assert mock_display.called
            html = mock_display.call_args[0][0]._repr_html_()
            assert test_str in html


def test_snakeviz_config_unsupported_option(shell):
    with pytest.raises(error.UsageError, match="option -r not recognized"):
        shell.run_line_magic("snakeviz_config", "-r")
