from bs4 import BeautifulSoup
from typing import Optional
from ..models import ClassworkReport, Course, Assignment

def parse_classwork(html_content: str, student_id: Optional[str] = None) -> ClassworkReport:
    soup = BeautifulSoup(html_content, 'html.parser')
    report = ClassworkReport(student_id=student_id, courses=[])
    
    # Typical HAC structure: each class is inside a div with class 'AssignmentClass'
    # or similar 'sg-content-grid' blocks
    course_divs = soup.find_all('div', class_='AssignmentClass')
    
    if not course_divs:
        # Fallback to look for general tables if AssignmentClass is not used
        # We'll just do a best-effort structural parsing
        pass

    for div in course_divs:
        course_header_tag = div.find('a', class_='sg-header-heading')
        course_name = course_header_tag.text.strip() if course_header_tag else "Unknown Course"
        
        # Sometime the average is in a span with a specific ID or class near the header
        average = None
        score_tags = div.find_all('span', class_='sg-header-heading')
        for tag in score_tags:
            text = tag.text.strip()
            if "%" in text:
                try:
                    average = float(text.replace("%", "").strip())
                except ValueError:
                    pass

        course = Course(name=course_name, average=average, assignments=[])
        
        # Look for the assignments table
        table = div.find('table', class_='sg-asp-table')
        if table:
            # First row is usually headers
            rows = table.find_all('tr')
            if len(rows) > 1:
                # Assuming standard HAC column positions if we can't find explicitly:
                # Date Due | Date Assigned | Assignment | Category | Score | Total Points
                headers = [th.text.strip().lower() for th in rows[0].find_all('th')]
                
                for row in rows[1:]:
                    cols = row.find_all('td')
                    if len(cols) >= 6:
                        # Extract data safely
                        date_due = cols[0].text.strip()
                        date_assigned = cols[1].text.strip()
                        name_tag = cols[2].find('a')
                        name = name_tag.text.strip() if name_tag else cols[2].text.strip()
                        category = cols[3].text.strip()
                        score_text = cols[4].text.strip()
                        total_points_text = cols[5].text.strip()
                        
                        score = None
                        if score_text and score_text.replace('.', '', 1).isdigit():
                            score = float(score_text)
                            
                        max_points = None
                        if total_points_text and total_points_text.replace('.', '', 1).isdigit():
                            max_points = float(total_points_text)
                            
                        course.assignments.append(
                            Assignment(
                                name=name,
                                category=category,
                                date_assigned=date_assigned if date_assigned else None,
                                date_due=date_due if date_due else None,
                                max_points=max_points,
                                score=score,
                                notes=""
                            )
                        )
        
        report.courses.append(course)
        
    return report
