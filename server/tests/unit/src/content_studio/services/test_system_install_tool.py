"""Trabajo de instalación asistida de herramientas del sistema."""

import sys

from content_studio.system import tools


def test_ac6_uses_an_argv_and_reports_the_installation_result(tmp_path, monkeypatch, capsys):
    from content_studio.services.registry import SERVICES

    assert 'system.install_tool' in SERVICES
    service = SERVICES['system.install_tool']
    assert service.build_command({'name': 'git'}, tmp_path) == [
        sys.executable,
        '-m',
        'content_studio.services.system_install_tool',
        'git',
    ]
    assert service.validate({'name': 'other'})[0]['code'] == 'unknown_system_tool'
    monkeypatch.setattr(tools, 'install_tool', lambda name: {'installed': name == 'git'})
    assert service.run('git') == 0
    assert service.run('ffmpeg') == 1
    assert '"installed": true' in capsys.readouterr().out
