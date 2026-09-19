# South African English formats; Django ships none for en-za and falls back to US English.
DATE_FORMAT = "j M Y"
SHORT_DATE_FORMAT = "Y-m-d"
DATETIME_FORMAT = "j M Y H:i"
SHORT_DATETIME_FORMAT = "Y-m-d H:i"
TIME_FORMAT = "H:i"
DATE_INPUT_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%d %b %Y"]
DATETIME_INPUT_FORMATS = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M"]
FIRST_DAY_OF_WEEK = 1
DECIMAL_SEPARATOR = "."
THOUSAND_SEPARATOR = "\u00a0"
NUMBER_GROUPING = 3
