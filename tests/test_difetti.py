"""Test della versione 0.7.0: i tre difetti trovati da Code. Il fuso senza la tabella dei fusi (a), il recap
con voci_diario = 0 (b), il file del blocco fuori dal quaderno (c). Solo dati inventati."""

import io
import json
import tempfile
import unittest
import zoneinfo
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from hypomnema import blocco, cambiamenti, configurazione, controllo, fuso_europeo, sportello
from hypomnema.cli import FUSO_CON_REGOLA, FUSO_CON_TABELLA, main
from tests.esecutore import CONFIG_DI_PROVA, fuso_disponibile, fuso_come_con_la_tabella

ADESSO = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone(timedelta(hours=1)))
UTC = timezone.utc


def senza_tabella(nome):
    raise zoneinfo.ZoneInfoNotFoundError(f"No time zone found with key {nome}")


class ConCartella(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.cartella = Path(self._tmp.name).resolve()

    def config(self, fuso: str | None = None, aggiunta: str = "") -> Path:
        testo = CONFIG_DI_PROVA
        if fuso is not None:
            testo = testo.replace("cifre_numero_nota = 4\n", f'cifre_numero_nota = 4\nfuso = "{fuso}"\n')
        file = self.cartella / "hypomnema.toml"
        file.write_text(testo + aggiunta, encoding="utf-8")
        return file

    def lancia(self, config: Path, *comando, adesso=ADESSO):
        uscita = io.StringIO()
        codice = main(["--config", str(config), *comando], adesso=adesso, uscita=uscita, errori=uscita)
        return codice, uscita.getvalue()


class TestFusoSenzaTabella(ConCartella):
    def con_la_regola(self, nome: str):
        with mock.patch.object(zoneinfo, "ZoneInfo", senza_tabella):
            return configurazione.carica(str(self.config(nome)))

    def test_f1_f2_ora_legale_e_solare(self):
        config = self.con_la_regola("Europe/Rome")
        self.assertTrue(config.fuso_con_regola)
        self.assertEqual(configurazione.nel_fuso(config, datetime(2026, 7, 14, 22, 30, tzinfo=UTC)).isoformat(),
                         "2026-07-15T00:30:00+02:00")
        self.assertEqual(configurazione.nel_fuso(config, datetime(2026, 1, 14, 23, 30, tzinfo=UTC)).isoformat(),
                         "2026-01-15T00:30:00+01:00")

    def test_f3_i_passaggi_d_ora(self):
        rome = fuso_europeo.FusoEuropeo("Europe/Rome")
        for universale, atteso in (
            (datetime(2026, 3, 29, 0, 59, tzinfo=UTC), "2026-03-29T01:59:00+01:00"),
            (datetime(2026, 3, 29, 1, 0, tzinfo=UTC), "2026-03-29T03:00:00+02:00"),
            (datetime(2026, 10, 25, 0, 59, tzinfo=UTC), "2026-10-25T02:59:00+02:00"),
            (datetime(2026, 10, 25, 1, 0, tzinfo=UTC), "2026-10-25T02:00:00+01:00"),
        ):
            with self.subTest(universale=universale):
                self.assertEqual(universale.astimezone(rome).isoformat(), atteso)

    @unittest.skipUnless(fuso_disponibile(), "su questo computer manca la tabella dei fusi orari")
    def test_f4_la_regola_e_la_tabella_dicono_lo_stesso(self):
        """Dal 2025 al 2027: Rome, London e Athens ogni mezz'ora; tutti i fusi dell'elenco ogni 6 ore e, nei giorni
        dei passaggi d'ora, ogni mezz'ora."""
        def ore(passo_ore: float, giorni=None):
            ora = datetime(2025, 1, 1, tzinfo=UTC)
            while ora.year < 2028:
                if giorni is None or ora.date() in giorni:
                    yield ora
                ora += timedelta(hours=passo_ore)
        passaggi = {d.date() for anno in (2025, 2026, 2027) for d in fuso_europeo._passaggi(anno)}
        for nome in fuso_europeo.ORA_SOLARE:
            if not fuso_disponibile(nome):
                continue  # un nome vecchio che la tabella di questo computer non ha più
            tabella, regola = zoneinfo.ZoneInfo(nome), fuso_europeo.FusoEuropeo(nome)
            fitto = nome in ("Europe/Rome", "Europe/London", "Europe/Athens")
            with self.subTest(fuso=nome):
                for ora in (ore(0.5) if fitto else (*ore(6), *ore(0.5, passaggi))):
                    a, b = ora.astimezone(tabella), ora.astimezone(regola)
                    self.assertEqual((a.isoformat(), a.fold), (b.isoformat(), b.fold), ora)

    def test_f5_fuori_elenco_errore_e_niente_scritto(self):
        proposta = self.cartella / "p.json"
        proposta.write_text(json.dumps({"date": "2026-01-15", "source": "s", "author": "user", "knowledge": "stated",
                                        "kind": "fact", "text": "x"}), encoding="utf-8")
        config = self.config("America/New_York")
        with mock.patch.object(zoneinfo, "ZoneInfo", senza_tabella):
            codice, uscita = self.lancia(config, "propose", str(proposta))
        self.assertEqual(codice, 2)
        self.assertIn("il fuso non è tra quelli europei che il programma sa calcolare da sé", uscita)
        self.assertIn("Non ho scritto niente.", uscita)
        self.assertFalse((self.cartella / "quaderno").exists())

    def test_f6_status_nei_tre_casi(self):
        self.assertIn("\nFuso orario: quello del computer.\n", self.lancia(self.config(), "status")[1])
        with mock.patch.object(zoneinfo, "ZoneInfo", senza_tabella):
            _, uscita = self.lancia(self.config("Europe/Rome"), "status")
        self.assertIn("\nFuso orario: Europe/Rome (funziona, con la regola europea dell'ora legale scritta nel "
                      "programma: su questo computer manca la tabella dei fusi).\n", uscita)
        self.assertEqual(fuso_come_con_la_tabella(uscita).count(FUSO_CON_TABELLA), 1)
        if fuso_disponibile():
            _, uscita = self.lancia(self.config("Europe/Rome"), "status")
            self.assertIn("\nFuso orario: Europe/Rome (funziona, con la tabella dei fusi del computer).\n", uscita)
            self.assertNotIn(FUSO_CON_REGOLA, uscita)


class TestVociDiarioZero(ConCartella):
    def test_d1_niente_blocco_del_diario(self):
        config = self.config(aggiunta='\n[recap]\nvoci_diario = 0\n')
        self.assertEqual(configurazione.carica(str(config)).recap_voci_diario, 0)
        codice, uscita = self.lancia(config, "recap")
        self.assertEqual(codice, 0)
        self.assertNotIn("diario", uscita)
        self.assertTrue(uscita.endswith("Ultime decisioni: nessuna.\n\nLegenda: F fatto · I idea · D decisione · "
                                        "O aperta · T da fare · ✓ chiusa\n"))

    def test_gli_altri_blocchi_restano_maggiori_di_zero(self):
        for chiave in ("discorsi_aperti", "todo", "decisioni"):
            with self.subTest(chiave=chiave):
                with self.assertRaisesRegex(configurazione.ErroreConfigurazione, "maggiore di zero"):
                    configurazione.carica(str(self.config(aggiunta=f'\n[recap]\n{chiave} = 0\n')))
        with self.assertRaisesRegex(configurazione.ErroreConfigurazione, "zero o più"):
            configurazione.carica(str(self.config(aggiunta='\n[recap]\nvoci_diario = -1\n')))


class TestBloccoFuoriDalQuaderno(ConCartella):
    def proposta(self) -> bytes:
        return json.dumps({"date": "2026-01-15", "source": "s", "author": "user", "knowledge": "stated",
                           "kind": "fact", "text": "Una nota."}).encode("utf-8")

    def test_l1_nel_quaderno_solo_nota_e_registro(self):
        config = configurazione.carica(str(self.config()))
        self.assertTrue(sportello.ricevi(self.proposta(), "p.json", config, ADESSO).accettata)
        quaderno = self.cartella / "quaderno"
        self.assertEqual(sorted(p.relative_to(quaderno).as_posix() for p in quaderno.rglob("*")),
                         ["note", "note/0001.md", "registro.md"])
        file = blocco.file_del_blocco(quaderno)
        self.assertEqual(file.parent, Path(tempfile.gettempdir()) / "hypomnema-blocchi")
        self.assertEqual(file.read_bytes(), b"")

    def test_lo_stesso_quaderno_da_due_percorsi_uguali(self):
        quaderno = self.cartella / "quaderno"
        self.assertEqual(blocco.file_del_blocco(quaderno), blocco.file_del_blocco(self.cartella / "x" / ".." / "quaderno"))
        self.assertNotEqual(blocco.file_del_blocco(quaderno), blocco.file_del_blocco(self.cartella / "altro"))

    def test_l3_quaderno_della_0_6_1_con_il_vecchio_file(self):
        config = configurazione.carica(str(self.config()))
        sportello.ricevi(self.proposta(), "p.json", config, ADESSO)
        vecchio = self.cartella / "quaderno" / ".sportello.lock"
        vecchio.write_bytes(b"")
        istantanea = cambiamenti.istantanea(config)
        self.assertNotIn(".sportello.lock", json.dumps(istantanea))
        sportello.ricevi(self.proposta(), "p.json", config, ADESSO)
        istantanea = cambiamenti.leggi_istantanea(json.dumps(istantanea).encode("utf-8"))
        self.assertEqual([c.percorso for c in cambiamenti.cambiati(config, istantanea)],
                         ["note/0002.md", "registro.md"])
        self.assertTrue(controllo.controlla(config).in_ordine)
        self.assertEqual(vecchio.read_bytes(), b"")

    def test_cartella_temporanea_senza_permessi_si_va_avanti(self):
        config = configurazione.carica(str(self.config()))
        with mock.patch.object(blocco, "file_del_blocco", return_value=self.cartella / "manca" / "x" / "b.lock"), \
                mock.patch.object(Path, "mkdir", side_effect=[None, PermissionError(13, "negato")]):
            with blocco.blocco(config.cartella_quaderno, crea=True):
                pass


if __name__ == "__main__":
    unittest.main()
