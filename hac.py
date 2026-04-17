#!/usr/bin/env python3
import os
import sys
import argparse
from dotenv import load_dotenv

from hac_client import CacheManager, to_markdown, to_sqlite

def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Test Harness for HAC Scraper")
    parser.add_argument('--username', help="HAC username", default=os.getenv('HAC_USERNAME'))
    parser.add_argument('--password', help="HAC password", default=os.getenv('HAC_PASSWORD'))
    parser.add_argument('--district-parser', help="HAC District (e.g. leander_isd)", default=os.getenv('HAC_DISTRICT_PARSER', 'leander_isd'))
    parser.add_argument('--student-id', help="Optional student ID to fetch", default=None)
    parser.add_argument('--format', choices=['markdown', 'sqlite', 'both'], default='both', help="Output format")
    parser.add_argument('--db-path', default='cache/hac_data.sqlite', help="Path for sqlite output")
    parser.add_argument('--md-path', default='cache/hac_data.md', help="Path to export markdown output")
    parser.add_argument('--force-refresh', action='store_true', help="Force a background cache refresh instead of honoring TTL")
    parser.add_argument('--skill', choices=['none', 'due_today', 'due_friday', 'due_sunday', 'due_next_week', 'missing_all', 'missing_last_week', 'missing_last_month', 'low_grades', 'low_class_grades'], default='none', help="Run an analytical skill")
    parser.add_argument('--skills', action='store_true', help="List all available analytical skills and exit")
    
    args = parser.parse_args()
    
    if args.skills:
        import sys
        print("Available analytical skills for --skill:")
        for s in ['due_today', 'due_friday', 'due_sunday', 'due_next_week', 'missing_all', 'missing_last_week', 'missing_last_month', 'low_grades', 'low_class_grades']:
            print(f"  - {s}")
        sys.exit(0)
    
    if not args.username or not args.password:
        print("Error: --username and --password (or HAC_USERNAME/HAC_PASSWORD env vars) are required.")
        return
        
    os.makedirs("cache", exist_ok=True)

    print("Fetching classwork data via CacheManager...")
    cache = CacheManager(cache_dir="cache")
    report = cache.get_classwork(
        username=args.username, 
        password=args.password, 
        student_id=args.student_id, 
        student_name="test_student",
        district_parser=args.district_parser,
        force_refresh=args.force_refresh
    )
    
    try:
        print(f"Extracted {len(report.courses)} courses.")
        if len(report.courses) == 0:
            print("Since 0 courses were extracted, saving raw HTML to cache/debug_classwork.html for parsing analysis.")
            
        if args.skill != 'none':
            from hac_client import skills
            print(f"\n--- Running Skill: {args.skill} ---")
            if args.skill == 'due_today':
                print(skills.assignments_due_today(report))
            elif args.skill == 'due_friday':
                print(skills.assignments_due_by_friday(report))
            elif args.skill == 'due_sunday':
                print(skills.assignments_due_by_sunday(report))
            elif args.skill == 'due_next_week':
                print(skills.assignments_due_in_next_week(report))
            elif args.skill == 'missing_all':
                print(skills.missing_assignments_all(report))
            elif args.skill == 'missing_last_week':
                print(skills.missing_assignments_last_week(report))
            elif args.skill == 'missing_last_month':
                print(skills.missing_assignments_last_month(report))
            elif args.skill == 'low_grades':
                print(skills.low_grades(report))
            elif args.skill == 'low_class_grades':
                print(skills.low_class_grades(report))
        else:
            if args.format in ['markdown', 'both']:
                print("\n--- BEGIN MARKDOWN ---")
                print(to_markdown(report))
                print("--- END MARKDOWN ---\n")
                with open(args.md_path, "w") as f:
                    f.write(to_markdown(report))
                print(f"Markdown saved to file at {args.md_path}")
                
            if args.format in ['sqlite', 'both']:
                to_sqlite(report, args.db_path)
                print(f"Data saved to SQLite database at {args.db_path}")

        if cache.last_thread and cache.last_thread.is_alive():
            print("\n[BACKGROUND] Background task spawned to refresh cache TTL. Waiting for thread to join...")
            cache.last_thread.join()
            print("[BACKGROUND] Cache update complete!")

    except Exception as e:
        print(f"Error occurred: {e}")

if __name__ == '__main__':
    main()
