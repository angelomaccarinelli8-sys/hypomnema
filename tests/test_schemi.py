"""Test della versione 0.9.0, pezzo 1: gli schemi del modo di parlare dell'utente e il suggerimento dello sportello.
Solo dati inventati."""

import unittest

from hypomnema import schemi
from hypomnema.cercatore import leggi
from tests.test_versioni import ConQuaderno


class ConNote(ConQuaderno):
    def utente(self, tipo, testo, **altro):
        return self.accettata(kind=tipo, text=testo, **altro)

    def claude(self, tipo, testo):
        return self.accettata(author="claude", knowledge="inferred", kind=tipo, text=testo)

    def conti(self):
        return schemi.Conti.da(schemi.note_dell_utente(leggi(self.config)))


class TestRegole(ConNote):
    def test_s1_s2_s3_quota_e_minimo(self):
        for testo in ("D'ora in poi annaffio io.", "D'ora in poi pago io.", "D'ora in poi cucino io."):
            self.utente("decision", testo)
        self.utente("idea", "D'ora in poi potremmo correre.")
        conti = self.conti()
        self.assertTrue(conti.tipica("d'ora in poi", "decision"))  # 3 decisioni su 4 note = 75%
        self.assertFalse(conti.tipica("d'ora in poi", "idea"))
        # «d'ora in» e «in poi» sono coppie «vuote» per la regola dello script (una parola e «in»).
        self.assertFalse(conti.tipica("d'ora in", "decision"))
        self.assertFalse(conti.tipica("in poi", "decision"))
        # S2: 2 decisioni e 2 idee: 50%, non è tipica di nessuno.
        for tipo in ("decision", "decision", "idea", "idea"):
            self.utente(tipo, "Forse domani sera.")
        conti = self.conti()
        self.assertFalse(any(conti.tipica("domani sera", t) for t in schemi.TIPI))
        # S3: in una sola decisione non basta.
        self.utente("decision", "Basta così, chiuso.")
        self.assertFalse(self.conti().tipica("basta così", "decision"))

    def test_s4_coppie_vuote(self):
        for _ in range(3):
            self.utente("decision", "Il vaso di casa resta.")
        conti = self.conti()
        self.assertFalse(conti.tipica("di casa", "decision"))
        self.assertTrue(conti.tipica("vaso di casa", "decision"))  # le sequenze di 3 parole non sono mai «vuote»
        self.assertTrue(conti.tipica("casa resta", "decision"))

    def test_s5_le_note_di_claude_non_contano(self):
        for _ in range(3):
            self.claude("idea", "Propongo di fare così.")
        self.assertEqual(self.conti().schemi("idea"), [])

    def test_s6_conta_la_prima_versione(self):
        self.utente("idea", "Magari un giorno si fa.")
        self.utente("idea", "Magari un giorno si fa.")
        self.accettata(updates="0001", kind="todo", text="Va fatto.")
        self.assertTrue(self.conti().tipica("magari un giorno", "idea"))

    def test_parole_come_lo_script(self):
        self.assertEqual(schemi.sequenze("D'ora in POI, 3 vasi!"),
                         frozenset({"d'ora in", "in poi", "d'ora in poi", "poi vasi", "in poi vasi"}))


class TestSuggerimento(ConNote):
    def setUp(self):
        super().setUp()
        for testo in ("D'ora in poi annaffio io.", "D'ora in poi pago io.", "D'ora in poi cucino io."):
            self.utente("decision", testo)

    def test_s7_suggerisce_e_non_cambia_niente(self):
        registro_prima = self.config.file_registro.read_text(encoding="utf-8")
        file = self.cartella / "p.json"
        file.write_text('{"date": "2026-01-15", "source": "s", "author": "user", "knowledge": "stated", '
                        '"kind": "idea", "text": "D\'ora in poi stendo io."}', encoding="utf-8")
        codice, uscita = self.comando("propose", str(file))
        self.assertEqual(codice, 0)
        self.assertTrue(uscita.endswith("SUGGERIMENTO (non cambia niente): suona come una decisione (decision: "
                                        "«d'ora in poi»). È giusto il tipo idea? Per cambiarlo serve "
                                        "updates.\n"))
        self.assertIn("- kind: idea\n", self.file_nota("0004"))
        self.assertNotIn("SUGGERIMENTO", self.file_nota("0004"))
        nuovo = self.config.file_registro.read_text(encoding="utf-8")[len(registro_prima):]
        self.assertRegex(nuovo, r"^- \S+ \| ACCETTATA \| nota 0004 \| da: p\.json\n$")

    def test_s7_anche_se_rifiutata(self):
        esito = self.proponi(kind="idea", text="D'ora in poi stendo io.", priority="urgent")
        self.assertFalse(esito.accettata)
        self.assertEqual(esito.suggerimento, ("decision", ["d'ora in poi"], "idea"))

    def test_s8_tipo_giusto_niente(self):
        self.assertIsNone(self.proponi(kind="decision", text="D'ora in poi stendo io.").suggerimento)

    def test_s9_senza_schemi_niente(self):
        self.assertIsNone(self.proponi(kind="idea", text="Parole mai viste prima.").suggerimento)

    def test_s10_a_parita_niente(self):
        for _ in range(3):
            self.utente("idea", "Magari un giorno chissà.")
        # Due sequenze tipiche di decision, due di idea: parità, nessun suggerimento.
        self.assertIsNone(self.proponi(kind="idea", text="D'ora in poi, magari un giorno.").suggerimento)

    def test_solo_note_nuove_dell_utente(self):
        self.assertIsNone(self.proponi(author="claude", knowledge="inferred", kind="idea",
                                       text="D'ora in poi stendo io.").suggerimento)
        self.assertIsNone(self.proponi(updates="0001", priority="high", text="D'ora in poi è urgente.").suggerimento)


class TestComando(ConNote):
    def setUp(self):
        super().setUp()
        for testo in ("D'ora in poi annaffio io.", "D'ora in poi pago io.", "Da adesso pago io."):
            self.utente("decision", testo)
        for testo in ("Magari un giorno il pozzo.", "Magari un giorno la serra."):
            self.utente("idea", testo)
        self.utente("todo", "Comprare il pane.")

    def test_s12_uscita_fissa(self):
        codice, uscita = self.comando("patterns")
        self.assertEqual(codice, 0)
        righe = uscita.splitlines()
        # «d'ora in», «in poi», «magari un», «un giorno»: coppie «vuote» (regola dello script).
        self.assertEqual(righe[2], "- decision (3 note): «d'ora in poi» 2, «pago io» 2")
        self.assertEqual(righe[3], "- idea (2 note): «magari un giorno» 2")
        self.assertEqual(righe[4], "- todo (1 nota): nessuno schema")
        self.assertEqual(self.comando("schemi")[1], uscita)

    def test_s11_misura(self):
        _, uscita = self.comando("patterns", "--misura")
        # Sulle stesse note: le 3 decisioni e le 2 idee hanno uno schema giusto, il todo nessuno.
        self.assertIn("Misura sulle stesse note (ottimista: gli schemi vengono anche dalla nota da indovinare): 6 note, "
                      "tipo giusto 5, nessuno schema 1, tipo sbagliato 0.", uscita)
        # A turno: togliendo una nota, le sue sequenze restano tipiche solo se compaiono in almeno altre 2 note.
        # Qui ogni schema ha solo 2 note: tolta una, ne resta 1, quindi nessuno schema per nessuna nota.
        self.assertIn("Misura a turno (onesta: ogni nota tolta dal calcolo prima di indovinarla): 6 note, tipo giusto 0, "
                      "nessuno schema 6, tipo sbagliato 0.", uscita)
        a = schemi.misura(schemi.note_dell_utente(leggi(self.config)), a_turno=True)
        b = schemi.misura(schemi.note_dell_utente(leggi(self.config)), a_turno=False)
        self.assertLessEqual(a.giuste, b.giuste)

    def test_misura_a_turno_con_piu_note(self):
        for testo in ("D'ora in poi stiro io.", "D'ora in poi lavo io."):
            self.utente("decision", testo)
        m = schemi.misura(schemi.note_dell_utente(leggi(self.config)), a_turno=True)
        # Le quattro decisioni con «d'ora in poi» ne hanno altre 3 a testa: giuste; le altre no.
        self.assertEqual((m.note, m.giuste, m.senza), (8, 4, 4))


if __name__ == "__main__":
    unittest.main()
