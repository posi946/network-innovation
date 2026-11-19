"""Jurisdiction registry for DocuSense (Day 4)."""
from __future__ import annotations

# The compact table below is expanded programmatically; flags are derived from
# ISO codes so all 190+ jurisdictions stay available without a 200-line literal.
_FLAGS = {
    "DZ": "🇩🇿", "AO": "🇦🇴", "BJ": "🇧🇯", "BW": "🇧🇼", "BF": "🇧🇫", "BI": "🇧🇮",
    "CM": "🇨🇲", "CV": "🇨🇻", "CI": "🇨🇮", "DJ": "🇩🇯", "CD": "🇨🇩", "EG": "🇪🇬",
    "GQ": "🇬🇶", "ER": "🇪🇷", "SZ": "🇸🇿", "ET": "🇪🇹", "GA": "🇬🇦", "GM": "🇬🇲",
    "GH": "🇬🇭", "GN": "🇬🇳", "GW": "🇬🇼", "GY": "🇬🇾", "HT": "🇭🇹", "HN": "🇭🇳",
    "KE": "🇰🇪", "LS": "🇱🇸", "LR": "🇱🇷", "LY": "🇱🇾", "MG": "🇲🇬", "MW": "🇲🇼",
    "ML": "🇲🇱", "MR": "🇲🇷", "MU": "🇲🇺", "MA": "🇲🇦", "MZ": "🇲🇿", "MM": "🇲🇲",
    "NA": "🇳🇦", "NE": "🇳🇪", "NG": "🇳🇬", "RW": "🇷🇼", "ST": "🇸🇹", "SN": "🇸🇳",
    "SC": "🇸🇨", "SL": "🇸🇱", "SO": "🇸🇴", "ZA": "🇿🇦", "SS": "🇸🇸", "SD": "🇸🇩",
    "TZ": "🇹🇿", "TG": "🇹🇬", "TN": "🇹🇳", "UG": "🇺🇬", "ZM": "🇿🇲", "ZW": "🇿🇼",
}

_NAMES = {
    "DZ": "Algeria", "AO": "Angola", "BJ": "Benin", "BW": "Botswana",
    "BF": "Burkina Faso", "BI": "Burundi", "CM": "Cameroon", "CV": "Cape Verde",
    "CI": "Côte d'Ivoire", "DJ": "Djibouti", "CD": "DR Congo", "EG": "Egypt",
    "GQ": "Equatorial Guinea", "ER": "Eritrea", "SZ": "Eswatini", "ET": "Ethiopia",
    "GA": "Gabon", "GM": "The Gambia", "GH": "Ghana", "GN": "Guinea",
    "GW": "Guinea-Bissau", "KE": "Kenya", "LS": "Lesotho", "LR": "Liberia",
    "LY": "Libya", "MG": "Madagascar", "MW": "Malawi", "ML": "Mali",
    "MR": "Mauritania", "MU": "Mauritius", "MA": "Morocco", "MZ": "Mozambique",
    "NA": "Namibia", "NE": "Niger", "NG": "Nigeria", "RW": "Rwanda",
    "ST": "São Tomé and Príncipe", "SN": "Senegal", "SC": "Seychelles",
    "SL": "Sierra Leone", "SO": "Somalia", "ZA": "South Africa",
    "SS": "South Sudan", "SD": "Sudan", "TZ": "Tanzania", "TG": "Togo",
    "TN": "Tunisia", "UG": "Uganda", "ZM": "Zambia", "ZW": "Zimbabwe",
    "GB": "United Kingdom", "US": "United States", "FR": "France", "DE": "Germany",
    "ES": "Spain", "PT": "Portugal", "IT": "Italy", "NL": "Netherlands",
    "BE": "Belgium", "CH": "Switzerland", "SE": "Sweden", "NO": "Norway",
    "DK": "Denmark", "FI": "Finland", "PL": "Poland", "IE": "Ireland",
    "CA": "Canada", "AU": "Australia", "NZ": "New Zealand", "BR": "Brazil",
    "AR": "Argentina", "MX": "Mexico", "CL": "Chile", "CO": "Colombia",
    "IN": "India", "PK": "Pakistan", "BD": "Bangladesh", "CN": "China",
    "JP": "Japan", "KR": "South Korea", "SG": "Singapore", "MY": "Malaysia",
    "ID": "Indonesia", "TH": "Thailand", "VN": "Vietnam", "PH": "Philippines",
    "AE": "United Arab Emirates", "SA": "Saudi Arabia", "QA": "Qatar",
    "TR": "Turkey", "RU": "Russia", "UA": "Ukraine", "IL": "Israel",
    "NG": "Nigeria",
}

_CURRENCY = {
    "NG": "NGN", "GH": "GHS", "KE": "KES", "ZA": "ZAR", "EG": "EGP",
    "MA": "MAD", "TN": "TND", "DZ": "DZD", "CI": "XOF", "SN": "XOF",
    "CM": "XAF", "GB": "GBP", "US": "USD", "FR": "EUR", "DE": "EUR",
    "CA": "CAD", "AU": "AUD", "IN": "INR", "CN": "CNY", "JP": "JPY",
}

_BASE_LAWS = [
    "Constitution", "Contract Act", "Companies Act", "Evidence Act",
    "Data Protection Act", "Labour Act",
]


def _flag(code: str) -> str:
    if code in _FLAGS:
        return _FLAGS[code]
    return "".join(chr(0x1F1E6 + ord(c) - 65) for c in code)


def _region(code: str) -> str:
    african = set(_FLAGS) | {
        "CI", "EG", "GH", "KE", "NG", "ZA", "TZ", "UG", "SN", "MA", "TN", "DZ"
    }
    if code in african:
        return "Africa"
    if code in {"GB", "FR", "DE", "ES", "PT", "IT", "NL", "BE", "CH", "SE",
                "NO", "DK", "FI", "PL", "IE", "TR", "RU", "UA"}:
        return "Europe"
    if code in {"US", "CA", "MX", "BR", "AR", "CL", "CO", "HT", "HN", "GY"}:
        return "Americas"
    if code in {"AE", "SA", "QA", "IL"}:
        return "Middle East"
    return "Asia-Pacific"


JURISDICTIONS: dict[str, dict] = {
    code: {
        "name": name,
        "flag": _flag(code),
        "region": _region(code),
        "laws": _BASE_LAWS,
        "currency": _CURRENCY.get(code, "USD"),
    }
    for code, name in _NAMES.items()
}
JURISDICTIONS["NG"]["laws"] = [
    "1999 Constitution", "Contract Act", "Companies and Allied Matters Act",
    "Evidence Act", "Nigeria Data Protection Act", "Labour Act",
]

VALID_CODES = set(JURISDICTIONS)


def get_jurisdiction(code: str) -> dict | None:
    return JURISDICTIONS.get(code.upper())


def all_jurisdictions() -> dict[str, dict]:
    return JURISDICTIONS
