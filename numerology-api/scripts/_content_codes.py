"""Static code lists for all 22 numerology content tables.

Kept separate so seed_content.py stays under 200 lines.
Each entry: (model_class, table_label, codes_list)
"""

# Standard master-number sets
_MASTER = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "11", "22", "33"]
_BASIC = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]

# BirthdayChart codes derived from Django views.py
_BIRTHDAY_CHART = [
    "1", "2", "3", "4", "5", "6", "7", "8", "9",
    "1_1", "1_2", "1_3", "1_4", "1_5",
    "2_1", "2_2", "2_3", "2_4", "2_5",
    "3_1", "3_2", "3_3", "3_4", "3_5",
    "4_1", "4_2", "4_3", "4_4", "4_5",
    "5_1", "5_2", "5_3", "5_4", "5_5",
    "6_1", "6_2", "6_3", "6_4", "6_5",
    "7_1", "7_2", "7_3", "7_4", "7_5",
    "8_1", "8_2", "8_3", "8_4", "8_5",
    "9_1", "9_2", "9_3", "9_4", "9_5",
    "1_single", "3_single", "7_single", "9_single",
    "123", "147", "159", "258", "357", "369", "456", "789",
    "not_147", "not_159", "not_258", "not_357", "not_369", "not_456", "not_789",
    "20  ",
]

# PhoneNumber: 2-digit zero-padded 00-99 + common 4-digit patterns
_PHONE_NUMBER = [f"{n:02d}" for n in range(100)] + [
    "1234", "5678", "6688", "8888", "9999",
]

# Table → codes mapping: (tablename_label, codes_list)
# Keys are used only for display; actual table driven by model in seed_content.py
CONTENT_CODES: dict[str, list[str]] = {
    "MainNumber":           _MASTER,
    "MissionNumber":        _MASTER,
    "ExecutionNumber":      _BASIC,
    "SoulsNumber":          _MASTER,
    "DevelopmentNumber":    _BASIC,
    "LifePeak":             _BASIC + ["11", "22", "33", "1000"],
    "ChallengeLife":        _BASIC,
    "BirthdayChart":        _BIRTHDAY_CHART,
    "NameChart":            _BASIC,
    "StagesOfLife":         ["1", "2", "3"],
    "AttitudeNumber":       _MASTER,
    "BirthdayNumber":       _BASIC,
    "MatureNumber":         _MASTER,
    "IntrospectiveNumber":  _MASTER,
    "KarmicNumber":         _BASIC,
    "DeficitNumber":        _BASIC,
    "PhoneNumber":          _PHONE_NUMBER,
    "PersonalMonthNumber":  _BASIC,
    "Identifiable":         _BASIC,
    "BalanceNumber":        _MASTER,
    "MissNumber":           _BASIC,
    "PersonalYearNumber":   [str(n) for n in range(1, 12)],  # 1-11
}
