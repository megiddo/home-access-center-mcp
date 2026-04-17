import os
import json
import threading
import time
from .client import HACClient
from .parsers import get_parser
from .models import ClassworkReport

class CacheManager:
    """
    Wraps the HACClient to provide eventually-consistent TTL caching.
    Always returns immediate JSON data if available. Updates the cache in the background.
    """
    def __init__(self, cache_dir: str):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        self.last_thread = None

    def get_classwork(self, username, password, student_id, student_name, district_parser, force_refresh=False) -> ClassworkReport:
        cache_file = os.path.join(self.cache_dir, f"{student_name}_classwork_cache.json")
        
        needs_update = force_refresh
        cache_exists = os.path.exists(cache_file)
        
        if cache_exists:
            # 3600 seconds = 60 minutes
            mtime = os.path.getmtime(cache_file)
            if time.time() - mtime > 3600:
                needs_update = True
        else:
            needs_update = True
            
        report = None
        if cache_exists:
            with open(cache_file, "r") as f:
                data = json.load(f)
                report = ClassworkReport(**data)
                
        if needs_update:
            if not cache_exists:
                # Must block if we have no old data to return at all
                self._fetch_and_cache(username, password, student_id, district_parser, cache_file)
                with open(cache_file, "r") as f:
                    report = ClassworkReport(**json.load(f))
            else:
                # Return old data immediately, but spawn thread to update cache
                thread = threading.Thread(
                    target=self._fetch_and_cache, 
                    args=(username, password, student_id, district_parser, cache_file)
                )
                thread.daemon = True
                thread.start()
                self.last_thread = thread
                
        return report
        
    def _fetch_and_cache(self, username, password, student_id, district_parser, cache_file):
        try:
            client = HACClient(username, password)
            if client.login():
                html = client.get_classwork(student_id=student_id)
                parser_fn = get_parser(district_parser)
                report = parser_fn(html, student_id=student_id)
                
                with open(cache_file, "w") as f:
                    f.write(report.model_dump_json())
            else:
                print(f"Background cache update failed: Login unverified for student {student_id}")
        except Exception as e:
            # Silently fail background fetches (LLM will just retry later or rely on older cache)
            print(f"Background cache update failed: {e}")
