"""Utility functions for the elderdocs application.

This module bundles together common helper functions used across the
application, such as date parsing, citizen ID validation, filename
sanitisation and PII masking. Keeping these utilities in a single place
makes them easier to test and maintain.
"""

from __future__ import annotations

import datetime as dt
import re
import unicodedata
from pathlib import Path
from typing import Dict, Optional, Tuple

from app.config import get_config


def parse_thai_date(date_str: str) -> Optional[dt.date]:
    """Parse a date string that may contain Thai month names and Buddhist Era years.

    The function supports both full and abbreviated Thai month names. When a
    two‑digit year is provided it is assumed to be a Buddhist year in the
    range 2500–2599. Four‑digit years of 2400 and above are treated as
    Buddhist years and converted to the Gregorian calendar by subtracting
    543. If conversion fails the function returns ``None``.

    Parameters
    ----------
    date_str: str
        A date string such as "1 มกราคม 2565" or "15 ก.พ. 61".

    Returns
    -------
    Optional[datetime.date]
        A ``date`` object if parsing succeeds, otherwise ``None``.
    """
    if not date_str or not isinstance(date_str, str):
        return None
    app_config, _ = get_config()
    month_full = app_config.get("thai_month_full", {})
    month_abbr = app_config.get("thai_month_abbr", {})
    # Normalise whitespace
    tokenised = date_str.strip().split()
    if len(tokenised) < 3:
        return None
    day_part, month_part, year_part = tokenised[0], tokenised[1], tokenised[2]
    # Convert day to int
    try:
        day = int(re.sub(r"[^0-9]", "", day_part))
    except ValueError:
        return None
    # Determine month index from Thai names or numeric
    month = None
    if month_part in month_full:
        month = int(month_full[month_part])
    elif month_part in month_abbr:
        month = int(month_abbr[month_part])
    else:
        # Fallback: try to parse numeric month
        try:
            month = int(month_part)
        except ValueError:
            return None
    # Normalise year. Remove any non‑digit characters.
    year_digits = re.sub(r"[^0-9]", "", year_part)
    if not year_digits:
        return None
    year = int(year_digits)
    # Interpret Buddhist Era years
    if year >= 2400:
        year -= 543
    elif year < 100:
        year += 2500
        year -= 543
    try:
        return dt.date(year, month, day)
    except ValueError:
        return None


def validate_thai_cid(cid: str) -> bool:
    """Validate a Thai citizen ID number using its checksum.

    A valid Thai ID consists of 13 digits. The checksum is calculated by
    multiplying each of the first 12 digits by weights descending from 13 to
    2, summing the results, computing ``11 - (sum % 11)``, and then taking
    ``result % 10``. The outcome must equal the 13th digit.

    Parameters
    ----------
    cid: str
        A string containing exactly 13 digits.

    Returns
    -------
    bool
        ``True`` if the ID is valid, otherwise ``False``.
    """
    if not cid or not re.fullmatch(r"\d{13}", cid):
        return False
    digits = [int(c) for c in cid]
    total = sum(d * w for d, w in zip(digits[:12], range(13, 1, -1)))
    checksum = (11 - (total % 11)) % 10
    return checksum == digits[-1]


def compute_age_years(dob: dt.date, reference_date: dt.date) -> Optional[int]:
    """Compute the age in years between two dates.

    Parameters
    ----------
    dob: datetime.date
        Date of birth.
    reference_date: datetime.date
        Date relative to which the age is computed (e.g. register date).

    Returns
    -------
    Optional[int]
        Age in complete years, or ``None`` if inputs are invalid.
    """
    # Validate inputs. ``datetime.date`` instances are expected; return ``None``
    # for any other types or missing values to avoid ``AttributeError`` at
    # runtime.
    if not isinstance(dob, dt.date) or not isinstance(reference_date, dt.date):
        return None

    # If the reference date precedes the date of birth the age would be
    # negative, which does not make sense in this context. Guard against this
    # by returning ``None`` instead of a negative value.
    if reference_date < dob:
        return None

    years = reference_date.year - dob.year
    # Adjust if birthday hasn't occurred yet this year
    if (reference_date.month, reference_date.day) < (dob.month, dob.day):
        years -= 1
    return years


# Pattern matching any characters disallowed in Windows filenames. Each match
# will be replaced individually so that sequences of illegal characters yield
# a corresponding number of underscores.
_ILLEGAL_FILENAME_CHARS = re.compile(r'[\\/:*?"<>|]')


def sanitize_filename(filename: str, max_length: int = 120) -> str:
    """Sanitise a filename by removing illegal characters and trimming length.

    Windows filesystems do not allow certain characters in filenames and have
    length limits. This function strips such characters, normalises Unicode
    characters to NFC form, and truncates the result to ``max_length``
    characters. If the resulting filename is empty, ``unnamed`` is returned.

    Parameters
    ----------
    filename: str
        The original filename to sanitise.
    max_length: int, optional
        Maximum allowed length of the returned filename (default 120).

    Returns
    -------
    str
        A safe filename suitable for use on most filesystems.
    """
    if not filename:
        return "unnamed"
    # Normalise to composed form to avoid hidden combining characters
    safe = unicodedata.normalize("NFC", filename)
    # Remove illegal characters
    safe = _ILLEGAL_FILENAME_CHARS.sub("_", safe)
    # Trim whitespace from ends
    safe = safe.strip()
    # Limit length
    if len(safe) > max_length:
        base, ext = Path(safe).stem, Path(safe).suffix
        max_base_len = max_length - len(ext)
        base = base[:max_base_len]
        safe = base + ext
    return safe or "unnamed"


def mask_pii(message: str) -> str:
    """Mask personally identifiable information in a log message.

    The patterns used for masking are defined in the configuration file. Each
    matched substring is replaced by asterisks to prevent sensitive data
    leakage. This function can be used manually when logging sensitive data.

    Parameters
    ----------
    message: str
        The message potentially containing PII.

    Returns
    -------
    str
        The message with PII masked.
    """
    _, mask_patterns = get_config()
    for pattern in mask_patterns.values():
        regex = re.compile(pattern)
        message = regex.sub("***", message)
    return message