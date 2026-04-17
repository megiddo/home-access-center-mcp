#!/usr/bin/env python3
import os
import json
import tempfile
from mcp.server.fastmcp import FastMCP
from typing import Union
from hac_client import CacheManager, to_markdown, to_sqlite, ClassworkReport, skills

# Create the FastMCP server
mcp = FastMCP("HAC Scraper")

# Load configuration and role limits from environment
# Standard practice for MCP servers launched by hosts
CONFIG_PATH = os.environ.get("HAC_CONFIG_PATH", "hac_config.json")
ALLOWED_STUDENTS = os.environ.get("HAC_ALLOWED_STUDENTS", "all")

def load_config():
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"Configuration file not found: {CONFIG_PATH}")
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def _fetch_base_classwork(student_name: str, force_refresh: bool) -> Union[ClassworkReport, str]:
    """Helper method to handle auth and return either the classwork report model or an error string."""
    student_name = student_name.lower().strip()
    
    # Authorize agent call
    allowed = [s.strip().lower() for s in ALLOWED_STUDENTS.split(",")]
    if "all" not in allowed and student_name not in allowed:
        return f"Access Denied: This agent is not authorized to access data for '{student_name}'."
        
    try:
        config = load_config()
    except Exception as e:
        return f"Configuration Error: {str(e)}"
        
    students = config.get("students", {})
    logins = config.get("logins", {})
        
    if student_name not in students:
        return f"Student '{student_name}' is not configured. Available students: {list(students.keys())}"
        
    login_id = students[student_name]
    if login_id not in logins:
        return f"Login profile '{login_id}' for student '{student_name}' is missing from the logins section."
        
    login_details = logins[login_id]
    username = login_details.get("username")
    password = login_details.get("password")
    student_id = None # Can be expanded in the future if needed
    district_parser = config.get("district_parser", "leander_isd")
    
    cache = CacheManager(cache_dir="cache")
    try:
        report = cache.get_classwork(
            username=username, 
            password=password, 
            student_id=student_id, 
            student_name=student_name,
            district_parser=district_parser,
            force_refresh=force_refresh
        )
        return report
    except Exception as e:
        return f"Fetch Error: {str(e)}"

@mcp.tool()
def get_student_classwork(student_name: str, force_refresh: bool = False, output_format: str = "markdown") -> str:
    """
    Logs into Home Access Center (HAC), scrapes the student's classwork page, and returns the raw data.
    
    This tool natively caches data for 60 minutes for rapid response times. 
    
    Args:
        student_name: The simple name of the student to fetch classwork for (e.g. 'billy')
        force_refresh: ONLY SET THIS TO TRUE if you MUST force an update right now, such as right after school lets out or if the user explicitly suspects the data is outdated. The cache is automatically eventually consistent, so default to False.
        output_format: 'markdown' to return a formatted table, or 'sqlite' to return a path to a sqlite DB.
    """
    report = _fetch_base_classwork(student_name, force_refresh)
    if isinstance(report, str):
        return report # Error string
        
    if not report.courses:
        return "No courses found on the classwork page."
        
    if output_format == "sqlite":
        # Create a temp file
        fd, db_path = tempfile.mkstemp(suffix=".sqlite")
        import os
        os.close(fd)
        to_sqlite(report, db_path)
        return f"Data successfully scraped and saved to SQLite Database: {db_path}\nYou may now query this database using sqlite tools."
        
    return to_markdown(report)

@mcp.tool()
def get_assignments_due_today(student_name: str, force_refresh: bool = False) -> str:
    """Gets a specific markdown list of all assignments due exactly today for this student."""
    report = _fetch_base_classwork(student_name, force_refresh)
    if isinstance(report, str): return report
    return skills.assignments_due_today(report)

@mcp.tool()
def get_assignments_due_by_friday(student_name: str, force_refresh: bool = False) -> str:
    """Gets a specific markdown list of all assignments due between today and the upcoming Friday."""
    report = _fetch_base_classwork(student_name, force_refresh)
    if isinstance(report, str): return report
    return skills.assignments_due_by_friday(report)

@mcp.tool()
def get_assignments_due_by_sunday(student_name: str, force_refresh: bool = False) -> str:
    """Gets a specific markdown list of all assignments due between today and the upcoming Sunday."""
    report = _fetch_base_classwork(student_name, force_refresh)
    if isinstance(report, str): return report
    return skills.assignments_due_by_sunday(report)

@mcp.tool()
def get_assignments_due_next_week(student_name: str, force_refresh: bool = False) -> str:
    """Gets a specific markdown list of all assignments due between today and exactly 7 days from now."""
    report = _fetch_base_classwork(student_name, force_refresh)
    if isinstance(report, str): return report
    return skills.assignments_due_in_next_week(report)

@mcp.tool()
def get_missing_assignments_all(student_name: str, force_refresh: bool = False) -> str:
    """Gets a list of ALL assignments where the due date has already passed and no score is currently recorded, indicating missing work."""
    report = _fetch_base_classwork(student_name, force_refresh)
    if isinstance(report, str): return report
    return skills.missing_assignments_all(report)

@mcp.tool()
def get_missing_assignments_last_week(student_name: str, force_refresh: bool = False) -> str:
    """Gets a list of assignments due strictly within the LAST 7 DAYS where no score is currently recorded."""
    report = _fetch_base_classwork(student_name, force_refresh)
    if isinstance(report, str): return report
    return skills.missing_assignments_last_week(report)

@mcp.tool()
def get_missing_assignments_last_month(student_name: str, force_refresh: bool = False) -> str:
    """Gets a list of assignments due strictly within the LAST 30 DAYS where no score is currently recorded."""
    report = _fetch_base_classwork(student_name, force_refresh)
    if isinstance(report, str): return report
    return skills.missing_assignments_last_month(report)

@mcp.tool()
def get_low_grades(student_name: str, threshold: float = 79.0, force_refresh: bool = False) -> str:
    """Gets a list of specific assignments where the student scored below the given threshold (default 79.0/C-)."""
    report = _fetch_base_classwork(student_name, force_refresh)
    if isinstance(report, str): return report
    return skills.low_grades(report, threshold=threshold)

@mcp.tool()
def get_low_class_grades(student_name: str, threshold: float = 79.0, force_refresh: bool = False) -> str:
    """Gets a list of courses where the student's overall class average is below the given threshold (default 79.0/C-)."""
    report = _fetch_base_classwork(student_name, force_refresh)
    if isinstance(report, str): return report
    return skills.low_class_grades(report, threshold=threshold)

if __name__ == "__main__":
    # FastMCP run starts stdio communication by default when executed directly
    mcp.run()
