"""Timezone constants and UTC conversion helpers."""
from datetime import datetime
from zoneinfo import ZoneInfo

TZ_BRAZIL = ZoneInfo("America/Sao_Paulo")
TZ_URUGUAY = ZoneInfo("America/Montevideo")
TZ_UTC = ZoneInfo("UTC")

SOURCE_TIMEZONES: dict[str, ZoneInfo] = {
    "santander_br": TZ_BRAZIL,
    "xp_br": TZ_BRAZIL,
    "bbva_uy": TZ_URUGUAY,
}


def to_utc(dt: datetime, source: str) -> datetime:
    """Localise a naive datetime using the source's default timezone, then convert to UTC."""
    tz = SOURCE_TIMEZONES[source]
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=tz)
    return dt.astimezone(TZ_UTC)
