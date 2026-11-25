"""Spec 029, fase 1: `studio mcp`, el subcomando del servidor por stdio."""

import argparse
from pathlib import Path

from content_studio.cli import mcp


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='studio')
    sub = parser.add_subparsers(dest='command')
    mcp.add_parser(sub, lambda: argparse.ArgumentParser(add_help=False))
    return parser


def test_studio_mcp_is_registered_without_options():
    assert _parser().parse_args(['mcp']).command == 'mcp'


def test_without_mcp_package_exits_2_and_says_so(monkeypatch, capsys):
    def missing_sdk(db: Path) -> None:
        raise ImportError("No module named 'mcp'")

    monkeypatch.setattr('content_studio.mcp_server.bridge.run_stdio', missing_sdk)
    assert mcp.dispatch(argparse.Namespace(db=Path('content-studio.db'))) == 2
    assert 'studio mcp needs the mcp package' in capsys.readouterr().err
