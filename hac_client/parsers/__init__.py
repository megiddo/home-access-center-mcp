from typing import Callable
from ..models import ClassworkReport
from typing import Optional

def get_parser(district_name: str) -> Callable[[str, Optional[str]], ClassworkReport]:
    """
    Returns the appropriate classwork parsing function for a given district.
    """
    district_name = district_name.lower().strip()
    
    if district_name == "leander_isd":
        from .leander_isd import parse_classwork
        return parse_classwork
        
    # Default fallback to the standard eSchoolPlus/HAC parser (often the same as Leander ISD)
    from .leander_isd import parse_classwork
    return parse_classwork
