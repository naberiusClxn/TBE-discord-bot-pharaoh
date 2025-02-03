import re

def parse_duration(duration: str) -> int:
    pattern = re.compile(r"^(\d+)([smhd])$")
    match = pattern.fullmatch(duration)
    if not match:
        return None
    value = int(match.group(1))
    unit = match.group(2)
    if unit == "s":
        return value
    elif unit == "m":
        return value * 60
    elif unit == "h":
        return value * 3600
    elif unit == "d":
        return value * 86400
    return None
