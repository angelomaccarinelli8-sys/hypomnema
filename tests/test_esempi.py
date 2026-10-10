"""Confronta ogni esempio con il suo risultato atteso (approvato da Angelo)."""

import tempfile
import unittest
from pathlib import Path

from tests.esecutore import elenco_esempi, esegui, file_di


class TestEsempi(unittest.TestCase):
    def test_ci_sono_gli_esempi(self):
        self.assertGreaterEqual(len(elenco_esempi()), 5)

    def test_ogni_esempio_da_il_risultato_atteso(self):
        for esempio in elenco_esempi():
            with self.subTest(esempio=esempio.name), tempfile.TemporaryDirectory() as tmp:
                lavoro = Path(tmp)
                uscita = esegui(esempio, lavoro)
                atteso = esempio / "atteso"
                self.assertEqual(uscita, (atteso / "uscita.txt").read_text(encoding="utf-8"))
                self.assertEqual(file_di(lavoro / "quaderno"), file_di(atteso / "quaderno"))


if __name__ == "__main__":
    unittest.main()
