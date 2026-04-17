from datetime import datetime, timedelta, date
from typing import List, Optional
from .models import ClassworkReport, Course, Assignment

def _parse_date(date_str: str) -> Optional[date]:
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str.strip(), "%m/%d/%Y").date()
    except ValueError:
        return None

def _format_assignment_list_md(title: str, items: List[tuple[Course, Assignment]]) -> str:
    if not items:
        return f"## {title}\nNo assignments found."
        
    md = [f"## {title}"]
    md.append("| Course | Assignment | Due Date | Score |")
    md.append("|---|---|---|---|")
    for course, assign in items:
        score_str = str(assign.score) if assign.score is not None else ""
        due_str = assign.date_due if assign.date_due else ""
        md.append(f"| {course.name} | {assign.name} | {due_str} | {score_str} |")
    return "\n".join(md)

def assignments_due_today(report: ClassworkReport, cur_date: Optional[date] = None) -> str:
    cur_date = cur_date or date.today()
    results = []
    for course in report.courses:
        for assign in course.assignments:
            d = _parse_date(assign.date_due)
            if d == cur_date:
                results.append((course, assign))
    return _format_assignment_list_md(f"Assignments Due Today ({cur_date.strftime('%m/%d/%Y')})", results)

def assignments_due_by_friday(report: ClassworkReport, cur_date: Optional[date] = None) -> str:
    cur_date = cur_date or date.today()
    # Friday is weekday 4 (0 is Monday). Calculate the upcoming Friday. 
    # If today is Saturday (5) or Sunday (6), it will get the NEXT Friday.
    days_to_friday = (4 - cur_date.weekday()) % 7
    friday_date = cur_date + timedelta(days=days_to_friday)
    results = []
    for course in report.courses:
        for assign in course.assignments:
            d = _parse_date(assign.date_due)
            if d and cur_date <= d <= friday_date:
                results.append((course, assign))
    return _format_assignment_list_md(f"Assignments Due by Friday ({friday_date.strftime('%m/%d/%Y')})", results)

def assignments_due_by_sunday(report: ClassworkReport, cur_date: Optional[date] = None) -> str:
    cur_date = cur_date or date.today()
    # Sunday is weekday 6
    days_to_sunday = (6 - cur_date.weekday()) % 7
    sunday_date = cur_date + timedelta(days=days_to_sunday)
    results = []
    for course in report.courses:
        for assign in course.assignments:
            d = _parse_date(assign.date_due)
            if d and cur_date <= d <= sunday_date:
                results.append((course, assign))
    return _format_assignment_list_md(f"Assignments Due by Sunday ({sunday_date.strftime('%m/%d/%Y')})", results)

def assignments_due_in_next_week(report: ClassworkReport, cur_date: Optional[date] = None) -> str:
    cur_date = cur_date or date.today()
    next_week_date = cur_date + timedelta(days=7)
    results = []
    for course in report.courses:
        for assign in course.assignments:
            d = _parse_date(assign.date_due)
            if d and cur_date <= d <= next_week_date:
                results.append((course, assign))
    return _format_assignment_list_md(f"Assignments Due in Next Week (by {next_week_date.strftime('%m/%d/%Y')})", results)

def _missing_assignments(report: ClassworkReport, cur_date: Optional[date] = None, days_back: Optional[int] = None) -> str:
    cur_date = cur_date or date.today()
    results = []
    
    start_date = None
    if days_back is not None:
        start_date = cur_date - timedelta(days=days_back)
        
    for course in report.courses:
        for assign in course.assignments:
            d = _parse_date(assign.date_due)
            # Treat an assignment as missing if due date is passed AND score is None (no grade recorded)
            if d and d < cur_date and assign.score is None:
                if start_date is None or d >= start_date:
                    results.append((course, assign))
                    
    title = "Missing Assignments"
    if days_back == 7:
        title += " (Due in the last 7 days)"
    elif days_back == 30:
        title += " (Due in the last 30 days)"
    else:
        title += " (All Time)"
        
    return _format_assignment_list_md(title, results)

def missing_assignments_all(report: ClassworkReport, cur_date: Optional[date] = None) -> str:
    return _missing_assignments(report, cur_date, days_back=None)

def missing_assignments_last_week(report: ClassworkReport, cur_date: Optional[date] = None) -> str:
    return _missing_assignments(report, cur_date, days_back=7)

def missing_assignments_last_month(report: ClassworkReport, cur_date: Optional[date] = None) -> str:
    return _missing_assignments(report, cur_date, days_back=30)

def low_grades(report: ClassworkReport, threshold: float = 79.0) -> str:
    results = []
    for course in report.courses:
        for assign in course.assignments:
            if assign.score is not None and assign.score < threshold:
                results.append((course, assign))
    return _format_assignment_list_md(f"Low Assignment Grades (Below {threshold})", results)

def low_class_grades(report: ClassworkReport, threshold: float = 79.0) -> str:
    md = [f"## Low Class Grades (Below {threshold})"]
    found = False
    for course in report.courses:
        if course.average is not None and course.average < threshold:
            if not found:
                md.append("| Course | Average |")
                md.append("|---|---|")
                found = True
            md.append(f"| {course.name} | {course.average} |")
            
    if not found:
        return md[0] + "\nNo low class grades found."
    return "\n".join(md)
