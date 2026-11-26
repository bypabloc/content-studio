"""Spec 032, D-4: certificado autofirmado junto a la base, creado una vez, con su huella SHA-256."""

from __future__ import annotations

import hashlib
import ssl

from content_studio.lan import cert


def test_ensure_creates_the_pair_once(tmp_path):
    cert_path, key_path = cert.ensure(tmp_path, '127.0.0.2')
    first = cert_path.read_bytes()

    again = cert.ensure(tmp_path, '192.168.1.20')

    assert again == (cert_path, key_path)
    assert cert_path.read_bytes() == first
    assert key_path.is_file()


def test_fingerprint_is_the_sha256_of_the_der(tmp_path):
    cert_path, _ = cert.ensure(tmp_path, '127.0.0.2')
    der = ssl.PEM_cert_to_DER_cert(cert_path.read_text(encoding='ascii'))

    assert cert.fingerprint(cert_path) == cert.format_fingerprint(hashlib.sha256(der).hexdigest())


def test_without_a_certificate_there_is_no_fingerprint(tmp_path):
    assert cert.fingerprint(tmp_path / 'lan-cert.pem') is None


def test_the_certificate_loads_as_a_tls_server_identity(tmp_path):
    cert_path, key_path = cert.ensure(tmp_path, '127.0.0.2')
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

    context.load_cert_chain(cert_path, key_path)
