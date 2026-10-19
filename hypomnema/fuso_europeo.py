"""L'ora legale europea scritta nel programma, per i computer senza la tabella dei fusi. Dalla 0.7.0.

Su Windows Python spesso non ha la tabella dei fusi orari (il pacchetto ``tzdata`` non c'è), e
allora ``fuso = "Europe/Rome"`` non si troverebbe. Per un elenco fisso di fusi europei che seguono
la regola dell'Unione Europea il programma sa fare da sé:

- l'ora solare è quella dell'elenco (+0, +1 o +2 rispetto all'ora universale);
- l'ora legale è un'ora in più, dall'ultima domenica di marzo all'ultima domenica di ottobre,
  sempre alle 01:00 di ora universale (la stessa ora in tutta l'Unione).

È la regola in vigore dal 1996. Se cambiasse, va cambiato questo file. Se la tabella dei fusi c'è,
si usa sempre quella (``configurazione._fuso``); fuori dall'elenco, senza tabella, è un errore.
"""

from datetime import date, datetime, timedelta, tzinfo

_UN_ORA = timedelta(hours=1)

# Il nome del fuso e la sua ora solare (ore rispetto all'ora universale).
ORA_SOLARE = {
    **{nome: 0 for nome in ("Europe/London", "Europe/Dublin", "Europe/Lisbon", "Atlantic/Canary",
                            "Atlantic/Madeira", "Atlantic/Faroe")},
    **{nome: 1 for nome in (
        "Europe/Rome", "Europe/Zurich", "Europe/Paris", "Europe/Berlin", "Europe/Madrid", "Europe/Vienna",
        "Europe/Amsterdam", "Europe/Brussels", "Europe/Luxembourg", "Europe/Monaco", "Europe/San_Marino",
        "Europe/Vatican", "Europe/Malta", "Europe/Ljubljana", "Europe/Zagreb", "Europe/Prague",
        "Europe/Bratislava", "Europe/Budapest", "Europe/Warsaw", "Europe/Copenhagen", "Europe/Stockholm",
        "Europe/Oslo", "Europe/Vaduz", "Europe/Andorra", "Europe/Gibraltar", "Europe/Belgrade",
        "Europe/Sarajevo", "Europe/Skopje", "Europe/Podgorica", "Europe/Tirane", "Europe/Busingen",
        "Arctic/Longyearbyen",
    )},
    **{nome: 2 for nome in (
        "Europe/Athens", "Europe/Helsinki", "Europe/Bucharest", "Europe/Sofia", "Europe/Riga",
        "Europe/Tallinn", "Europe/Vilnius", "Europe/Kiev", "Europe/Kyiv", "Europe/Mariehamn",
        "Asia/Nicosia", "Europe/Nicosia", "Europe/Chisinau",
    )},
}


def _ultima_domenica(anno: int, mese: int) -> date:
    fine = date(anno, mese, 31)
    return fine - timedelta(days=(fine.weekday() - 6) % 7)


def _passaggi(anno: int) -> tuple[datetime, datetime]:
    """Inizio e fine dell'ora legale, in ora universale (senza fuso)."""
    return (datetime.combine(_ultima_domenica(anno, 3), datetime.min.time()) + _UN_ORA,
            datetime.combine(_ultima_domenica(anno, 10), datetime.min.time()) + _UN_ORA)


class FusoEuropeo(tzinfo):
    """Un fuso europeo con la regola dell'ora legale dell'Unione Europea."""

    def __init__(self, nome: str):
        self.nome = nome
        self._solare = timedelta(hours=ORA_SOLARE[nome])

    def _legale_universale(self, universale: datetime) -> bool:
        inizio, fine = _passaggi(universale.year)
        return inizio <= universale < fine

    def fromutc(self, dt: datetime) -> datetime:
        universale = dt.replace(tzinfo=None)
        spostamento = self._solare + (_UN_ORA if self._legale_universale(universale) else timedelta(0))
        # L'ora che in ottobre si ripete: la seconda volta è già ora solare (fold = 1, come zoneinfo).
        _, fine = _passaggi(universale.year)
        ripetuta = 1 if fine <= universale < fine + _UN_ORA else 0
        return (universale + spostamento).replace(tzinfo=self, fold=ripetuta)

    def utcoffset(self, dt: datetime | None) -> timedelta:
        return self._solare + self.dst(dt)

    def dst(self, dt: datetime | None) -> timedelta:
        if dt is None:
            return timedelta(0)
        # Un'ora locale: si porta all'ora universale con l'ora solare. Nell'ora che si ripete in
        # ottobre vale la prima (ora legale), come fa zoneinfo con fold = 0.
        locale = dt.replace(tzinfo=None)
        inizio, fine = _passaggi(locale.year)
        if inizio + self._solare <= locale < fine + self._solare + _UN_ORA * (1 - getattr(dt, "fold", 0)):
            return _UN_ORA
        return timedelta(0)

    def tzname(self, dt: datetime | None) -> str:
        return self.nome

    def __repr__(self) -> str:
        return f"FusoEuropeo({self.nome!r})"


def fuso(nome: str) -> tzinfo | None:
    """Il fuso con la regola europea, oppure None se il nome non è nell'elenco."""
    return FusoEuropeo(nome) if nome in ORA_SOLARE else None

