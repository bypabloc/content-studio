"""Checkout principal (spec 004, D-3): desde un worktree, la carpeta que contiene el .git común."""

from __future__ import annotations

from content_studio import paths
from content_studio.common.checkout import main_checkout


def test_main_checkout_holds_the_common_git_dir():
    assert (main_checkout(paths.ROOT) / '.git').exists()
