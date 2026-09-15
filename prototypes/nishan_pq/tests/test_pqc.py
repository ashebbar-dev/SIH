from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from nishan import pqc


@unittest.skipUnless(pqc.support().ready, "OpenSSL PQC provider is unavailable")
class PQCTests(unittest.TestCase):
    def test_ml_kem_round_trip_and_ml_dsa_tamper_detection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            kem_private = root / "kem-private.pem"
            kem_public = root / "kem-public.pem"
            pqc.generate_keypair("ML-KEM-768", kem_private, kem_public)
            ciphertext, sender_secret = pqc.encapsulate(kem_public)
            self.assertEqual(sender_secret, pqc.decapsulate(kem_private, ciphertext))
            self.assertEqual(len(sender_secret), 32)

            sign_private = root / "sign-private.pem"
            sign_public = root / "sign-public.pem"
            pqc.generate_keypair("ML-DSA-65", sign_private, sign_public)
            message = b"canonical decryption event"
            signature = pqc.sign(sign_private, message)
            self.assertTrue(pqc.verify(sign_public, message, signature))
            self.assertFalse(pqc.verify(sign_public, message + b"!", signature))


if __name__ == "__main__":
    unittest.main()

