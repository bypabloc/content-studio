"""Certificado autofirmado de la red local (spec 032, D-4): se crea una vez junto a la base y su huella lo identifica.

`cryptography` se importa dentro de la función: `studio --help` no la necesita.
"""

from __future__ import annotations

import hashlib
import ipaddress
import ssl
from datetime import UTC, datetime, timedelta
from pathlib import Path

CERT_NAME = 'lan-cert.pem'
KEY_NAME = 'lan-key.pem'
VALID_DAYS = 3650


def ensure(folder: Path, address: str) -> tuple[Path, Path]:
    """Las rutas del certificado y la clave; los crea si faltan (no se rehacen: la huella fijada sigue valiendo)."""
    cert_path, key_path = folder / CERT_NAME, folder / KEY_NAME
    if cert_path.is_file() and key_path.is_file():
        return cert_path, key_path
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.x509.oid import NameOID

    key = ec.generate_private_key(ec.SECP256R1())
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'Content Studio LAN')])
    now = datetime.now(UTC)
    names = [x509.IPAddress(ipaddress.ip_address(address)), x509.DNSName('localhost')]
    certificate = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=5))
        .not_valid_after(now + timedelta(days=VALID_DAYS))
        .add_extension(x509.SubjectAlternativeName(names), critical=False)
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(key, hashes.SHA256())
    )
    folder.mkdir(parents=True, exist_ok=True)
    key_path.write_bytes(
        key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
    )
    cert_path.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
    return cert_path, key_path


def fingerprint(cert_path: Path) -> str | None:
    """La huella SHA-256 del certificado, o None si todavía no existe."""
    if not cert_path.is_file():
        return None
    der = ssl.PEM_cert_to_DER_cert(cert_path.read_text(encoding='ascii'))
    return format_fingerprint(hashlib.sha256(der).hexdigest())


def format_fingerprint(hexdigest: str) -> str:
    """La huella como la muestran los navegadores: pares en mayúsculas separados por dos puntos.

    >>> format_fingerprint('0a1b2c')
    '0A:1B:2C'
    """
    upper = hexdigest.upper()
    return ':'.join(upper[index : index + 2] for index in range(0, len(upper), 2))
