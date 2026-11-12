"""News addon configuration: which symbols and sources a product monitors, and when. Data only.

The file holds no thresholds, prompts or scoring rules; those belong to the licensed addon.
"""
from __future__ import annotations

from datetime import date, timedelta
import re
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .common import Refused, fields, require, timestamp
from .packages import IDENTIFIER, PAYLOAD_FIELDS, SYMBOL, validate_payload

CONFIG_FIELDS = ("product_id", "package_id", "monitor_from", "epoch_end", "timezone", "symbols", "sources")
DATE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
TIMEZONE = re.compile(r"^[A-Za-z][A-Za-z0-9_+-]{0,31}(/[A-Za-z0-9_+-]{1,32}){0,2}$")
SOURCE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,63}$")
MAX_SYMBOLS = 100
MAX_SOURCES = 50
MAX_ALIASES = 10


def calendar_date(value, what):
    require(isinstance(value, str) and DATE.fullmatch(value), f"{what} must be a YYYY-MM-DD date")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise Refused(f"{what} must be a YYYY-MM-DD date") from exc


def time_zone(name):
    require(isinstance(name, str) and TIMEZONE.fullmatch(name),
            "timezone must be an IANA time zone name such as America/New_York")
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError, OSError) as exc:
        raise Refused(f"Unknown time zone: {name}") from exc


def validate_news_config(config, payload=None):
    """Check a news configuration, and with a payload, that it fits that edition."""
    fields(config, CONFIG_FIELDS)
    for name in ("product_id", "package_id"):
        require(isinstance(config[name], str) and IDENTIFIER.fullmatch(config[name]), f"Invalid {name}")
    first = calendar_date(config["monitor_from"], "monitor_from")
    last = calendar_date(config["epoch_end"], "epoch_end")
    require(first <= last, "monitor_from must not be later than epoch_end")
    zone = time_zone(config["timezone"])
    symbols = config["symbols"]
    require(isinstance(symbols, dict) and 1 <= len(symbols) <= MAX_SYMBOLS,
            f"symbols maps 1 to {MAX_SYMBOLS} symbols")
    for symbol, entry in symbols.items():
        require(SYMBOL.fullmatch(symbol), "Invalid symbol")
        fields(entry, ("cik", "aliases"))
        cik = entry["cik"]
        require(cik is None or (type(cik) is int and 1 <= cik <= 9_999_999_999),
                "cik is a positive integer of at most 10 digits, or null")
        aliases = entry["aliases"]
        require(isinstance(aliases, list) and 1 <= len(aliases) <= MAX_ALIASES and
                all(isinstance(alias, str) and 0 < len(alias) <= 100 for alias in aliases) and
                len(aliases) == len(set(aliases)),
                f"Each symbol has 1 to {MAX_ALIASES} distinct aliases of 1 to 100 characters")
    sources = config["sources"]
    require(isinstance(sources, dict) and 1 <= len(sources) <= MAX_SOURCES,
            f"sources maps 1 to {MAX_SOURCES} source names")
    for name, source in sources.items():
        require(SOURCE.fullmatch(name), "Source names use lowercase letters, digits, '.', '_' or '-'")
        fields(source, ("enabled",))
        require(type(source["enabled"]) is bool, "enabled is true or false")
    result = {"status": "valid", "product_id": config["product_id"], "package_id": config["package_id"],
              "symbols": len(symbols), "sources": len(sources),
              "enabled_sources": sum(source["enabled"] for source in sources.values())}
    if payload is None:
        return result
    fields(payload, PAYLOAD_FIELDS)
    validate_payload(payload, timestamp(payload["published_at"]))
    require(config["package_id"] == payload["package_id"], "The news configuration names another package")
    outside = sorted(set(symbols) - set(payload["universe"]))
    require(not outside, f"Symbols outside the payload universe: {', '.join(outside)}")
    try:
        final_day = (timestamp(payload["valid_until"]) - timedelta(microseconds=1)).astimezone(zone).date()
    except OverflowError:  # validity ends beyond the last representable local date
        final_day = date.max
    require(last <= final_day, f"epoch_end must not be later than valid_until ({final_day.isoformat()} "
                               f"in {config['timezone']})")
    return {**result, "edition_id": payload["edition_id"]}
