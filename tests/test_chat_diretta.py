"""Test della versione 0.6.1: la chat collegata al computer scrive direttamente sul quaderno vero.

Python 3.10 (la copia di tomli), il giro completo come lo fa la chat, due che scrivono insieme (il
blocco), gli stessi byte da Windows e da Linux. Solo dati inventati.
"""

import builtins
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from hypomnema import _tomli, archivio, blocco, cambiamenti, configurazione, controllo, sportello
from hypomnema.cli import main
from tests.esecutore import CONFIG_DI_PROVA, RADICE

ADESSO = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone(timedelta(hours=1)))
MODELLO_CHAT = RADICE / "chat" / "hypomnema-chat.toml"
CONFIG_CODE = CONFIG_DI_PROVA.replace("attivo = false", "attivo = true")


def proposta(**campi) -> bytes:
    nota = {"date": "2026-01-15", "source": "chat del 15 gennaio 2026", "author": "claude",
            "knowledge": "inferred", "kind": "idea", "text": "Una nota.", **campi}
    return json.dumps(nota, ensure_ascii=False).encode("utf-8")


class TestPython310(unittest.TestCase):
    def test_tomli_legge_come_tomllib(self):
        """La copia di tomli dà lo stesso risultato di tomllib su ogni file TOML del repository."""
        try:
            import tomllib
        except ImportError:
            self.assertIs(configurazione.tomllib, _tomli)  # Python 3.10: si usa la copia
            return
        file = sorted(RADICE.glob("*.toml")) + sorted(RADICE.glob("*/*.toml")) + sorted(RADICE.glob("esempi/*/*.toml"))
        self.assertGreater(len(file), 10)
        for percorso in file:
            with self.subTest(file=percorso.relative_to(RADICE).as_posix()):
                testo = percorso.read_text(encoding="utf-8")
                self.assertEqual(_tomli.loads(testo), tomllib.loads(testo))
        with self.assertRaises(_tomli.TOMLDecodeError):
            _tomli.loads("[quaderno\ncartella = 1")

    def test_copia_non_modificata_con_licenza(self):
        cartella = RADICE / "hypomnema" / "_tomli"
        self.assertIn("MIT License", (cartella / "LICENSE").read_text(encoding="utf-8"))
        self.assertEqual(_tomli.__version__, "2.0.1")
        self.assertIn("non modificata", (cartella / "LEGGIMI.md").read_text(encoding="utf-8"))

    def test_requisito_3_10(self):
        self.assertIn('requires-python = ">=3.10"', (RADICE / "pyproject.toml").read_text(encoding="utf-8"))


class CartellaDellUtente(unittest.TestCase):
    """La cartella Hypomnema dell'utente come la vede la chat: due configurazioni, un quaderno."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name).resolve()
        self.hypomnema = base / "mnt" / "Hypomnema"
        self.casa = base / "casa"  # la cartella personale della macchina della chat
        (self.hypomnema / "quaderno").mkdir(parents=True)
        self.casa.mkdir()
        (self.hypomnema / "hypomnema.toml").write_text(CONFIG_CODE, encoding="utf-8", newline="\n")
        self.config_code = self.hypomnema / "hypomnema.toml"
        self.config_chat = self.hypomnema / "hypomnema-chat.toml"

    def tearDown(self):
        self._tmp.cleanup()

    def copia_il_programma(self) -> Path:
        """Come «git clone … programma-chat»: i file del programma, senza le cartelle __pycache__."""
        programma = self.hypomnema / "programma-chat"
        for parte in ("hypomnema", "chat"):
            shutil.copytree(RADICE / parte, programma / parte, ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copyfile(RADICE / "programma.py", programma / "programma.py")
        return programma

    def lancia(self, programma: Path, *argomenti, config=None):
        """Come la chat: python3 -B …/programma.py --config …/hypomnema-chat.toml …"""
        ambiente = {k: v for k, v in os.environ.items() if k not in ("HYPOMNEMA_CONFIG", "PYTHONDONTWRITEBYTECODE")}
        ambiente.update(HOME=str(self.casa), PYTHONIOENCODING="utf-8")
        esito = subprocess.run(
            [sys.executable, "-B", str(programma / "programma.py"), "--config", str(config or self.config_chat),
             *argomenti],
            capture_output=True, cwd=self.casa, env=ambiente, timeout=60,
        )
        return esito.returncode, esito.stdout.decode("utf-8")


class TestGiroDellaChat(CartellaDellUtente):
    def test_giro_completo(self):
        programma = self.copia_il_programma()
        config_code_prima = self.config_code.read_bytes()
        # D2: la configurazione della chat nasce dal modello, senza sovrascrivere (cp -n).
        self.assertFalse(self.config_chat.exists())
        shutil.copyfile(programma / "chat" / "hypomnema-chat.toml", self.config_chat)

        codice, uscita = self.lancia(programma, "--version")
        self.assertEqual((codice, uscita.strip()), (0, "hypomnema 0.6.1"))
        # D3: status dice che è la configurazione della chat; check e recap sul quaderno vero.
        codice, uscita = self.lancia(programma, "status")
        self.assertIn("Testimone: NON C'È (configurazione per la chat di Claude)", uscita)
        self.assertEqual(self.lancia(programma, "check"), (0, "Quaderno in ordine: nessuna nota.\n"))
        self.assertEqual(self.lancia(programma, "recap")[0], 0)
        # D4: la proposta sta in un file temporaneo fuori dalla cartella collegata.
        temporanea = self.casa / "hypomnema-temp"
        temporanea.mkdir()
        (temporanea / "proposta.json").write_bytes(proposta(author="user", knowledge="stated", kind="fact",
                                                            text="Il limone sta meglio vicino alla finestra."))
        codice, uscita = self.lancia(programma, "propose", str(temporanea / "proposta.json"))
        self.assertEqual(codice, 0, uscita)
        self.assertTrue(uscita.startswith("ACCETTATA: la nota 0001 è stata salvata nel quaderno (note/0001.md)."))
        nota = (self.hypomnema / "quaderno" / "note" / "0001.md").read_text(encoding="utf-8")
        self.assertIn("- verification: author not verified (chat, no witness)\n", nota)
        self.assertEqual(self.lancia(programma, "check"),
                         (0, "Quaderno in ordine: 1 nota, con la sua riga ACCETTATA nel registro.\n"))
        # Niente toccato fuori dal quaderno, e nessuna cartella __pycache__ nella cartella collegata.
        self.assertEqual(self.config_code.read_bytes(), config_code_prima)
        self.assertEqual(list(self.hypomnema.rglob("__pycache__")), [])
        self.assertEqual(sorted(p.name for p in (self.hypomnema / "quaderno").iterdir()),
                         [".sportello.lock", "note", "registro.md"])
        self.assertEqual((self.hypomnema / "quaderno" / ".sportello.lock").read_bytes(), b"")

    def test_configurazione_sbagliata_si_vede_da_status(self):
        programma = self.copia_il_programma()
        _, uscita = self.lancia(programma, "status", config=self.config_code)
        self.assertNotIn("NON C'È", uscita)
        self.assertIn("Testimone: ACCESO", uscita)


def _proponi_in_un_processo(argomenti):
    """Una proposta in un processo a parte, come un'altra chat o un altro Claude Code."""
    cartella, config, numero = argomenti
    file = Path(cartella) / f"proposta-{numero}.json"
    file.write_bytes(proposta(text=f"Idea numero {numero}."))
    esito = subprocess.run([sys.executable, "-B", str(RADICE / "programma.py"), "--config", config, "propose", str(file)],
                           capture_output=True, timeout=120)
    return esito.returncode


class TestDueCheScrivonoInsieme(CartellaDellUtente):
    def setUp(self):
        super().setUp()
        shutil.copyfile(MODELLO_CHAT, self.config_chat)
        self.quaderno = self.hypomnema / "quaderno"

    def test_quaranta_proposte_insieme_da_due_configurazioni(self):
        lavori = [(str(self.casa), str(self.config_chat if i % 2 else self.config_code), i) for i in range(40)]
        with ThreadPoolExecutor(max_workers=20) as gruppo:
            codici = list(gruppo.map(_proponi_in_un_processo, lavori))
        self.assertEqual(codici, [0] * 40)
        note = sorted(p.name for p in (self.quaderno / "note").iterdir())
        self.assertEqual(note, [f"{n:04d}.md" for n in range(1, 41)])
        registro = (self.quaderno / "registro.md").read_text(encoding="utf-8")
        self.assertEqual(registro.count("# Registro degli ingressi"), 1)
        self.assertEqual(len(re.findall(r"\| ACCETTATA \| nota \d{4} \|", registro)), 40)
        testi = sorted(p.read_text(encoding="utf-8").split("## Text\n\n")[1].strip()
                       for p in (self.quaderno / "note").iterdir())
        self.assertEqual(testi, sorted(f"Idea numero {i}." for i in range(40)))  # nessuna sovrascritta
        self.assertTrue(controllo.controlla(configurazione.carica(str(self.config_code))).in_ordine)

    def test_dieci_chiusure_insieme_una_sola_entra(self):
        config = configurazione.carica(str(self.config_chat))
        sportello.ricevi(proposta(kind="todo", text="Rinvasare il limone."), "p.json", config, ADESSO)

        def chiudi(_):
            return sportello.ricevi(proposta(done="0001", kind=None, text="Rinvasato."), "c.json",
                                    configurazione.carica(str(self.config_chat)), ADESSO).accettata
        with ThreadPoolExecutor(max_workers=10) as gruppo:
            esiti = list(gruppo.map(chiudi, range(10)))
        self.assertEqual(esiti.count(True), 1)
        registro = (self.quaderno / "registro.md").read_text(encoding="utf-8")
        self.assertEqual(registro.count("already closed (✓T0001.1)"), 9)

    def test_quaderno_occupato(self):
        """Con il blocco tenuto da un altro processo lo sportello aspetta, poi si ferma senza scrivere."""
        sportello.ricevi(proposta(), "p.json", configurazione.carica(str(self.config_chat)), ADESSO)
        prima = {p.name: p.read_bytes() for p in self.quaderno.rglob("*") if p.is_file()}
        tieni = subprocess.Popen(
            [sys.executable, "-c", "import sys, time; sys.path.insert(0, sys.argv[1]);"
             "from pathlib import Path; from hypomnema import blocco;"
             "c = blocco.blocco(Path(sys.argv[2]), crea=True); c.__enter__(); print('preso', flush=True);"
             "time.sleep(30)", str(RADICE), str(self.quaderno)],
            stdout=subprocess.PIPE,
        )
        try:
            self.assertEqual(tieni.stdout.readline().strip(), b"preso")
            with mock.patch.object(blocco, "ATTESA_BLOCCO", 0.3):
                uscita = io.StringIO()
                file = self.casa / "proposta.json"
                file.write_bytes(proposta(text="Arriva mentre il quaderno è occupato."))
                codice = main(["--config", str(self.config_chat), "propose", str(file)], adesso=ADESSO, uscita=uscita)
            self.assertEqual(codice, 2)
            self.assertTrue(uscita.getvalue().startswith("ERRORE: il quaderno è occupato da un altro passaggio"))
            dopo = {p.name: p.read_bytes() for p in self.quaderno.rglob("*") if p.is_file()}
            self.assertEqual(dopo, prima)
        finally:
            tieni.kill()
            tieni.wait()

    def test_chi_legge_non_crea_il_blocco_e_cambiati_non_lo_riporta(self):
        config = configurazione.carica(str(self.config_chat))
        self.assertEqual(main(["--config", str(self.config_chat), "recap"], adesso=ADESSO, uscita=io.StringIO()), 0)
        self.assertFalse((self.quaderno / ".sportello.lock").exists())
        istantanea = json.dumps(cambiamenti.istantanea(config)).encode("utf-8")
        sportello.ricevi(proposta(), "p.json", config, ADESSO)
        self.assertEqual([c.percorso for c in cambiamenti.cambiati(config, cambiamenti.leggi_istantanea(istantanea))],
                         ["note/0001.md", "registro.md"])
        archivio.copia(config, json.dumps({"chat": "https://claude.ai/chat/esempio-inventato", "fuso": "UTC+01:00",
                                           "messaggi": [{"turno": 1, "quando": "Thu 2026-01-15 10:00", "chi": "utente",
                                                         "testo": "Ciao."}]}).encode("utf-8"))
        self.assertEqual((self.quaderno / ".sportello.lock").read_bytes(), b"")


class TestStessiByteDaWindowsELinux(unittest.TestCase):
    """La stessa proposta scritta «come Windows» e «come Linux» dà file identici byte per byte."""

    PROPOSTE = (
        dict(author="user", knowledge="stated", kind="todo", text="Rinvasare il limone.\nPrima di sabato.",
             context="Detto parlando del balcone, à è ò ù «virgolette»."),
        dict(author="claude", knowledge="inferred", kind="idea", text="Vaso più grande: 30 cm ⏎ forse.",
             quote="Rinvasare il limone."),
        dict(author="user", knowledge="stated", updates="0001", kind=None, priority="high", text="È urgente."),
        dict(author="user", knowledge="stated", done="0001", kind=None, text="Fatto: rinvasato.\nSabato."),
    )

    def scrivi_tutto(self, cartella: Path) -> dict[str, bytes]:
        (cartella / "hypomnema.toml").write_text(MODELLO_CHAT.read_text(encoding="utf-8"), encoding="utf-8",
                                                 newline="\n")
        config = configurazione.carica(str(cartella / "hypomnema.toml"))
        for i, campi in enumerate(self.PROPOSTE):
            # kind=None diventa «"kind": null», cioè un campo che manca: in un cambiamento si può.
            esito = sportello.ricevi(proposta(**campi), f"p{i}.json", config, ADESSO)
            self.assertTrue(esito.accettata, esito.motivi)
        archivio.copia(config, json.dumps({
            "chat": "https://claude.ai/chat/esempio-inventato", "fuso": "UTC+01:00",
            "messaggi": [{"turno": 1, "quando": "Thu 2026-01-15 10:00", "chi": "utente", "testo": "Ciao,\nà è."},
                         {"turno": 2, "quando": "Thu 2026-01-15 10:00", "chi": "claude", "testo": "Ciao «sì»."}],
        }, ensure_ascii=False).encode("utf-8"))
        quaderno = cartella / "quaderno"
        return {p.relative_to(quaderno).as_posix(): p.read_bytes() for p in sorted(quaderno.rglob("*")) if p.is_file()}

    def test_stessi_byte(self):
        apri = builtins.open

        def come_windows(file, mode="r", buffering=-1, encoding=None, errors=None, newline=None, *args, **kwargs):
            # Su Windows, senza scelte esplicite, Python scrive con la codifica del sistema e trasforma
            # ogni a capo in CR LF.
            if "b" not in mode:
                encoding = encoding or "cp1252"
                if newline is None and any(m in mode for m in "wax+"):
                    newline = "\r\n"
            return apri(file, mode, buffering, encoding, errors, newline, *args, **kwargs)

        with tempfile.TemporaryDirectory() as linux, tempfile.TemporaryDirectory() as windows:
            da_linux = self.scrivi_tutto(Path(linux))
            with mock.patch("builtins.open", come_windows), mock.patch("io.open", come_windows), \
                    mock.patch.object(os, "linesep", "\r\n"):
                da_windows = self.scrivi_tutto(Path(windows))
        self.assertEqual(sorted(da_linux), sorted(da_windows))
        self.assertIn("note/0001.1.md", da_linux)
        for nome in da_linux:
            with self.subTest(file=nome):
                self.assertEqual(da_windows[nome], da_linux[nome])
                self.assertNotIn(b"\r", da_linux[nome])
                da_linux[nome].decode("utf-8")  # sempre UTF-8

    def test_ogni_scrittura_ha_codifica_e_a_capo_espliciti(self):
        """Nel codice, ogni apertura di file in testo dice encoding="utf-8" e (in scrittura) newline="\\n"."""
        for file in sorted((RADICE / "hypomnema").glob("*.py")):
            testo = file.read_text(encoding="utf-8")
            for chiamata in re.finditer(r"\bopen\((?P<arg>[^)]*)\)|\.(?P<metodo>write_text|read_text)\((?P<arg2>[^)]*)\)",
                                        testo):
                arg = chiamata.group("arg") if chiamata.group("arg") is not None else chiamata.group("arg2")
                with self.subTest(file=file.name, chiamata=chiamata.group(0)):
                    if '"a+b"' in arg or '"rb"' in arg:
                        continue
                    self.assertIn('encoding="utf-8', arg)
                    if re.search(r'"[wax]"', arg) or chiamata.group("metodo") == "write_text":
                        self.assertIn('newline="\\n"', arg)


class TestDocumenti(unittest.TestCase):
    def test_skill_readme_storia(self):
        skill = (RADICE / "skills" / "hypomnema" / "SKILL.md").read_text(encoding="utf-8")
        for frammento in ("### C0. Chat connected to the computer", "python3 -B <HY>/programma-chat/programma.py",
                          "**you must never delete or overwrite files in the connected\nfolders**",
                          "`H status` must say `Testimone: NON C'È (configurazione per la chat di Claude)`",
                          "~/hypomnema-temp/proposta.json", "go on with C1-C5", "Python 3.10 or newer"):
            with self.subTest(frammento=frammento):
                self.assertIn(frammento, skill)
        readme = (RADICE / "README.md").read_text(encoding="utf-8")
        self.assertIn("### Chat collegata al computer: scrive direttamente sul quaderno (dalla 0.6.1)", readme)
        self.assertIn("programma-chat", readme)
        self.assertIn("## 0.6.1 (prototipo) — la chat scrive direttamente sul quaderno",
                      (RADICE / "STORIA.md").read_text(encoding="utf-8"))
        self.assertIn("`.sportello.lock`", (RADICE / "FORMATO.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
