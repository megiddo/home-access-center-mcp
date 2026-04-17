import requests
from bs4 import BeautifulSoup
from typing import Optional

class HACClient:
    LOGIN_URL = "https://lis-hac.eschoolplus.powerschool.com/HomeAccess/Account/LogOn?ReturnUrl=%2fHomeAccess"
    CLASSWORK_URL = "https://lis-hac.eschoolplus.powerschool.com/HomeAccess/Classes/Classwork"
    
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.session = requests.Session()
        
    def login(self) -> bool:
        # First get the login page to capture any anti-forgery tokens
        resp = self.session.get(self.LOGIN_URL)
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        token_input = soup.find('input', {'name': '__RequestVerificationToken'})
        
        payload = {
            'Database': '10',  # Common default for eSchoolPlus, might need to be dynamic or omitted
            'LogOnDetails.UserName': self.username,
            'LogOnDetails.Password': self.password,
            'user': self.username,
            'pass': self.password
        }
        
        if token_input:
            payload['__RequestVerificationToken'] = token_input['value']
            
        post_resp = self.session.post(self.LOGIN_URL, data=payload)
        post_resp.raise_for_status()
        
        # Determine if login was successful
        # Usually it redirects to HomeAccess/Classes or shows the user's name
        if "LogOn" in post_resp.url and "ReturnUrl" in post_resp.url:
            return False
            
        return True

    def get_classwork(self, student_id: Optional[str] = None) -> str:
        # If student_id is provided, we might need a context switch.
        # Often, HAC switches context via a POST to an endpoint, e.g. /HomeAccess/Frame/StudentPicker
        # For now, we will just request the classwork page directly.
        # If the user has multiple students, they may need to switch first.
        # Implementing the simple fetch:
        
        if student_id:
            # We add it as a query param if supported, though typically it's session-based.
            # E.g. /HomeAccess/Frame/StudentPicker?studentId=...
            # This is highly dependent on the district's implementation. Let's try appending for now.
            pass
            
        resp = self.session.get(self.CLASSWORK_URL)
        resp.raise_for_status()
        
        # Powerschool HAC often puts the actual assignments inside an iframe
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, 'html.parser')
        iframe = soup.find('iframe', id='sg-legacy-iframe')
        if iframe and iframe.has_attr('src'):
            src = iframe['src']
            # construct absolute url
            if src.startswith('/'):
                from urllib.parse import urlparse
                parsed = urlparse(self.CLASSWORK_URL)
                iframe_url = f"{parsed.scheme}://{parsed.netloc}{src}"
            else:
                iframe_url = src
                
            resp2 = self.session.get(iframe_url)
            resp2.raise_for_status()
            return resp2.text

        return resp.text
