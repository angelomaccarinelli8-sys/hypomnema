"""Test della versione 0.7.0: i tre difetti trovati da Code. Il fuso orario dal sistema operativo dell'utente (a),
il recap con voci_diario = 0 (b), il file del blocco fuori dal quaderno (c). Solo dati inventati."""

import io
import json
import tempfile
import unittest
import zoneinfo
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

import os
import sys
import types

from hypomnema import avvio, blocco, cambiamenti, configurazione, controllo, fuso_del_sistema, sportello
from hypomnema.cli import main
from hypomnema.fuso_del_sistema import Sistema
from tests.esecutore import CONFIG_DI_PROVA, fuso_disponibile, modello_chat

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


WINDOWS_ROMA = Sistema("Europe/Rome", "Windows: W. Europe Standard Time, regione IT")
MACCHINA_UTC = Sistema("Etc/UTC", "prova: macchina in UTC")


class TestNomeDelFusoDelSistema(unittest.TestCase):
    def test_windows_con_la_tabella_cldr(self):
        self.assertEqual(fuso_del_sistema.da_windows("W. Europe Standard Time", "IT"), "Europe/Rome")
        self.assertEqual(fuso_del_sistema.da_windows("W. Europe Standard Time", "CH"), "Europe/Zurich")
        self.assertEqual(fuso_del_sistema.da_windows("W. Europe Standard Time", None), "Europe/Berlin")
        self.assertEqual(fuso_del_sistema.da_windows("W. Europe Standard Time", "ZZ-sconosciuta"), "Europe/Berlin")
        self.assertEqual(fuso_del_sistema.da_windows("Eastern Standard Time", "US"), "America/New_York")
        self.assertEqual(fuso_del_sistema.da_windows("UTC", None), "Etc/UTC")
        self.assertIsNone(fuso_del_sistema.da_windows("Fuso Inventato", "IT"))

    def test_windows_dal_registro(self):
        """Il registro di Windows finto: chiave del fuso e regione."""
        valori = {r"SYSTEM\CurrentControlSet\Control\TimeZoneInformation": "W. Europe Standard Time",
                  r"Control Panel\International\Geo": "IT"}

        class Chiave:
            def __init__(self, percorso):
                self.percorso = percorso

            def __enter__(self):
                return self

            def __exit__(self, *errore):
                return False

        def apri(radice, percorso):
            if percorso not in valori:
                raise OSError("manca")
            return Chiave(percorso)

        finto = types.SimpleNamespace(HKEY_LOCAL_MACHINE=1, HKEY_CURRENT_USER=2, OpenKey=apri,
                                      QueryValueEx=lambda chiave, nome: (valori[chiave.percorso], 1))
        with mock.patch.dict(sys.modules, {"winreg": finto}):
            self.assertEqual(fuso_del_sistema._sistema_windows(), WINDOWS_ROMA)
            del valori[r"Control Panel\International\Geo"]
            self.assertEqual(fuso_del_sistema._sistema_windows(),
                             Sistema("Europe/Berlin", "Windows: W. Europe Standard Time"))

    def test_macos_e_linux(self):
        with tempfile.TemporaryDirectory() as cartella:
            cartella = Path(cartella)
            zona = cartella / "usr" / "share" / "zoneinfo" / "Europe"
            zona.mkdir(parents=True)
            (zona / "Rome").write_bytes(b"TZif")
            localtime = cartella / "localtime"
            timezone_file = cartella / "timezone"
            leggi = lambda ambiente: fuso_del_sistema._sistema_unix(ambiente, str(localtime), str(timezone_file))
            self.assertEqual(leggi({"TZ": ":Europe/Zurich"}).nome, "Europe/Zurich")
            self.assertIsNone(leggi({"TZ": "CET-1CEST"}).nome)  # una regola POSIX non è un nome
            self.assertIsNone(leggi({}).nome)
            timezone_file.write_text("Europe/Paris\n", encoding="utf-8")
            self.assertEqual(leggi({}).nome, "Europe/Paris")
            if hasattr(os, "symlink"):
                try:
                    os.symlink(zona / "Rome", localtime)
                except OSError:
                    return  # su Windows senza il permesso per i collegamenti
                self.assertEqual(leggi({}), Sistema("Europe/Rome", f"{localtime} → Europe/Rome"))

    def test_macchina_in_utc(self):
        for nome in ("UTC", "Etc/UTC", "Etc/Universal", "Zulu", "Etc/GMT"):
            self.assertTrue(fuso_del_sistema.in_utc(Sistema(nome, ""), ADESSO))
        for nome in ("Europe/Rome", "Europe/London", "Atlantic/Reykjavik"):
            self.assertFalse(fuso_del_sistema.in_utc(Sistema(nome, ""), datetime(2026, 1, 15, tzinfo=UTC)))
        # Nome che non si legge: decide la differenza dall'ora universale.
        self.assertTrue(fuso_del_sistema.in_utc(Sistema(None, ""), datetime(2026, 1, 15, tzinfo=UTC)))
        self.assertFalse(fuso_del_sistema.in_utc(Sistema(None, ""), ADESSO))


class ConSistema(ConCartella):
    def setUp(self):
        super().setUp()
        self.proposta = self.cartella / "p.json"
        self.proposta.write_text(json.dumps({"date": "2026-01-15", "source": "s", "author": "user",
                                             "knowledge": "stated", "kind": "fact", "text": "x"}), encoding="utf-8")

    def come(self, sistema: Sistema):
        return mock.patch.object(fuso_del_sistema, "leggi_sistema", return_value=sistema)

    def righe(self) -> list[dict]:
        file = self.cartella / "quaderno" / "fuso-del-sistema.jsonl"
        return [json.loads(r) for r in file.read_text(encoding="utf-8").splitlines()] if file.exists() else []

    def registro(self) -> str:
        return (self.cartella / "quaderno" / "registro.md").read_text(encoding="utf-8")


class TestComputerDellUtente(ConSistema):
    def test_vale_l_ora_del_sistema_e_il_fuso_si_scrive_nel_quaderno(self):
        config = self.config()
        with self.come(WINDOWS_ROMA):
            self.assertEqual(self.lancia(config, "propose", str(self.proposta))[0], 0)
            self.assertIn("- 2026-01-15T10:00:00+01:00 | ACCETTATA |", self.registro())
            self.assertEqual(self.righe(), [{"quando": "2026-01-15T10:00:00+01:00", "fuso": "Europe/Rome",
                                             "dal_sistema": "Windows: W. Europe Standard Time, regione IT"}])
            self.lancia(config, "propose", str(self.proposta))
            self.assertEqual(len(self.righe()), 1)  # stesso fuso: niente di nuovo
            _, stato = self.lancia(config, "status")
        self.assertIn("\nFuso orario: Europe/Rome, dal sistema operativo (Windows: W. Europe Standard Time, regione "
                      "IT).\n", stato)
        # Il file non è una nota e non tocca il registro: check resta in ordine.
        self.assertEqual(self.lancia(config, "check")[0], 0)

    def test_la_riga_fuso_non_conta_sul_computer_dell_utente(self):
        """Il taccuino con fuso = "Europe/Rome" aperto su un Windows senza tabella dei fusi: funziona."""
        config = self.config("Europe/Rome")
        with self.come(WINDOWS_ROMA), mock.patch.object(zoneinfo, "ZoneInfo", senza_tabella):
            codice, uscita = self.lancia(config, "propose", str(self.proposta))
            self.assertEqual(codice, 0, uscita)
            self.assertIn("- 2026-01-15T10:00:00+01:00 | ACCETTATA |", self.registro())
            _, stato = self.lancia(config, "status")
        self.assertIn("Fuso orario: Europe/Rome, dal sistema operativo", stato)
        config = self.config("Europe/Zurich")
        with self.come(WINDOWS_ROMA):
            _, stato = self.lancia(config, "status")
        self.assertIn('Nella configurazione c\'è fuso = "Europe/Zurich", diverso dal sistema: su questo computer vale '
                      "il sistema.", stato)

    def test_il_sistema_cambia_fuso(self):
        config = self.config()
        with self.come(WINDOWS_ROMA):
            self.lancia(config, "propose", str(self.proposta))
        with self.come(Sistema("America/New_York", "Windows: Eastern Standard Time, regione US")):
            self.lancia(config, "propose", str(self.proposta), adesso=ADESSO + timedelta(hours=1))
        with self.come(WINDOWS_ROMA):
            self.lancia(config, "propose", str(self.proposta), adesso=ADESSO + timedelta(hours=2))
        # Due computer che si alternano: una riga a ogni cambio, vale l'ultima.
        self.assertEqual([r["fuso"] for r in self.righe()], ["Europe/Rome", "America/New_York", "Europe/Rome"])
        self.assertEqual(fuso_del_sistema.ultima_riga(self.cartella / "quaderno").fuso, "Europe/Rome")

    def test_la_configurazione_della_chat_non_scrive_mai(self):
        config = modello_chat(self.cartella)
        with self.come(WINDOWS_ROMA):
            self.assertEqual(self.lancia(config, "propose", str(self.proposta))[0], 0)
        self.assertEqual(self.righe(), [])

    def test_a_inizio_sessione(self):
        config = self.config()
        (self.cartella / "quaderno").mkdir()
        with self.come(WINDOWS_ROMA):
            self.assertEqual(avvio.prepara(config), [])
            self.assertEqual(avvio.prepara(config), [])
        self.assertEqual(len(self.righe()), 1)
        with self.come(Sistema("Europe/London", "Windows: GMT Standard Time, regione GB")):
            self.assertEqual(avvio.prepara(config), ["Hypomnema: il fuso orario del sistema è cambiato (Europe/Rome → "
                                                     "Europe/London): l'ho scritto nel quaderno, così anche la chat "
                                                     "usa la tua ora."])

    def test_senza_quaderno_non_crea_niente(self):
        config = self.config()
        with self.come(WINDOWS_ROMA):
            avvio.prepara(config)
            self.lancia(config, "status")
        self.assertFalse((self.cartella / "quaderno").exists())


class TestMacchinaInUtc(ConSistema):
    def scrivi_il_file(self, fuso="Europe/Rome"):
        (self.cartella / "quaderno").mkdir(exist_ok=True)
        (self.cartella / "quaderno" / "fuso-del-sistema.jsonl").write_text(json.dumps(
            {"quando": "2026-01-10T09:00:00+01:00", "fuso": fuso, "dal_sistema": "prova"}) + "\n", encoding="utf-8")

    @unittest.skipUnless(fuso_disponibile(), "simula la macchina della chat, che ha la tabella dei fusi: qui manca")
    def test_il_fuso_dal_file_del_quaderno(self):
        self.scrivi_il_file()
        config = self.config()
        with self.come(MACCHINA_UTC):
            for adesso, giorno, ora in (
                (datetime(2026, 7, 14, 22, 30, tzinfo=UTC), "2026-07-15", "2026-07-15T00:30:00+02:00"),
                (datetime(2026, 1, 14, 23, 30, tzinfo=UTC), "2026-01-15", "2026-01-15T00:30:00+01:00"),
            ):
                self.assertEqual(self.lancia(config, "propose", str(self.proposta), adesso=adesso)[0], 0)
                self.assertIn(f"- {ora} | ACCETTATA |", self.registro())
                self.assertTrue(self.lancia(config, "recap", adesso=adesso)[1].startswith(
                    f"Dove eravamo rimasti (recap del {giorno})."))
            _, stato = self.lancia(config, "status")
        self.assertIn("\nFuso orario: Europe/Rome, dal file fuso-del-sistema.jsonl del quaderno (scritto il 2026-01-10 "
                      "dal computer dell'utente): questa macchina è in UTC.\n", stato)
        self.assertEqual(len(self.righe()), 1)  # la macchina in UTC non scrive mai il file

    @unittest.skipUnless(fuso_disponibile(), "simula la macchina della chat, che ha la tabella dei fusi: qui manca")
    def test_prima_la_riga_fuso_poi_il_file_poi_utc(self):
        self.scrivi_il_file()
        adesso = datetime(2026, 1, 14, 23, 30, tzinfo=UTC)
        with self.come(MACCHINA_UTC):
            _, stato = self.lancia(self.config("Europe/Athens"), "status", adesso=adesso)
            self.assertIn("Fuso orario: Europe/Athens, scritto nella configurazione: questa macchina è in UTC.", stato)
            self.lancia(self.config("Europe/Athens"), "propose", str(self.proposta), adesso=adesso)
            self.assertIn("- 2026-01-15T01:30:00+02:00 | ACCETTATA |", self.registro())
            with mock.patch.object(zoneinfo, "ZoneInfo", senza_tabella):
                codice, _ = self.lancia(self.config("Europe/Athens"), "propose", str(self.proposta), adesso=adesso)
                self.assertEqual(codice, 0)
                _, stato = self.lancia(self.config("Europe/Athens"), "status", adesso=adesso)
            self.assertIn("- 2026-01-14T23:30:00+00:00 | ACCETTATA |", self.registro())
            self.assertIn('Fuso orario: UTC, quello di questa macchina: fuso = "Europe/Athens" della configurazione non '
                          "si trova su questa macchina; il file fuso-del-sistema.jsonl dice Europe/Rome, ma su questa "
                          "macchina manca la tabella dei fusi.", stato)

    def test_senza_file_vale_utc_detto_chiaramente(self):
        with self.come(MACCHINA_UTC):
            _, stato = self.lancia(self.config(), "status")
        self.assertIn("\nFuso orario: UTC, quello di questa macchina: il quaderno non ha ancora il file "
                      "fuso-del-sistema.jsonl, che nasce la prima volta che usi Hypomnema sul tuo computer.\n", stato)

    def test_righe_rovinate_si_saltano(self):
        self.scrivi_il_file()
        with open(self.cartella / "quaderno" / "fuso-del-sistema.jsonl", "a", encoding="utf-8") as f:
            f.write("riga scritta a mano\n")
        self.assertEqual(fuso_del_sistema.ultima_riga(self.cartella / "quaderno").fuso, "Europe/Rome")


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
