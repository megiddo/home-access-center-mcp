import sqlite3
from typing import List
from .models import ClassworkReport, Course, Assignment

def to_markdown(report: ClassworkReport) -> str:
    md_lines = []
    
    md_lines.append(f"# Classwork Report")
    if report.student_id:
        md_lines.append(f"**Student ID**: {report.student_id}\n")
        
    for course in report.courses:
        avg_str = f"{course.average}%" if course.average is not None else "N/A"
        md_lines.append(f"## {course.name} (Average: {avg_str})")
        
        if not course.assignments:
            md_lines.append("_No assignments found._\n")
            continue
            
        md_lines.append("| Assignment | Category | Assigned | Due | Points | Score | Notes |")
        md_lines.append("|---|---|---|---|---|---|---|")
        
        for a in course.assignments:
            name = a.name.replace("|", r"\|")
            cat = a.category.replace("|", r"\|")
            assigned = str(a.date_assigned) if a.date_assigned else ""
            due = str(a.date_due) if a.date_due else ""
            max_p = str(a.max_points) if a.max_points is not None else ""
            score = str(a.score) if a.score is not None else ""
            notes = a.notes.replace("|", r"\|") if a.notes else ""
            
            md_lines.append(f"| {name} | {cat} | {assigned} | {due} | {max_p} | {score} | {notes} |")
            
        md_lines.append("") # blank line after table
        
    return "\n".join(md_lines)


def to_sqlite(report: ClassworkReport, db_path: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            name TEXT NOT NULL,
            average REAL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER,
            name TEXT NOT NULL,
            category TEXT,
            date_assigned TEXT,
            date_due TEXT,
            max_points REAL,
            score REAL,
            notes TEXT,
            FOREIGN KEY (course_id) REFERENCES courses(id)
        )
    """)
    
    # Clear existing data for this student_id (or generally clear if no student_id)
    # For a robust implementation, you might want UPSERT. Using simpler wipe-and-load for the test harness.
    if report.student_id:
        cursor.execute("DELETE FROM assignments WHERE course_id IN (SELECT id FROM courses WHERE student_id = ?)", (report.student_id,))
        cursor.execute("DELETE FROM courses WHERE student_id = ?", (report.student_id,))
    else:
        cursor.execute("DELETE FROM assignments")
        cursor.execute("DELETE FROM courses")

    for course in report.courses:
        cursor.execute("""
            INSERT INTO courses (student_id, name, average)
            VALUES (?, ?, ?)
        """, (report.student_id, course.name, course.average))
        course_id = cursor.lastrowid
        
        for a in course.assignments:
            cursor.execute("""
                INSERT INTO assignments (course_id, name, category, date_assigned, date_due, max_points, score, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (course_id, a.name, a.category, a.date_assigned, a.date_due, a.max_points, a.score, a.notes))
            
    conn.commit()
    conn.close()
