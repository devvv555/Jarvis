"""
J.A.R.V.I.S. Multi-Account Email Manager
Configured for:
1. Personal: devdarshanv2005@gmail.com
2. College:  26ab12@psgim.ac.in
"""

import os
import sys
import json
import imaplib
import email
from email.header import decode_header
from typing import List, Dict

ACCOUNTS_CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "email_accounts.json")

DEFAULT_ACCOUNTS = {
    "personal": {
        "email": "devdarshanv2005@gmail.com",
        "app_password": "",  # To be filled with 16-char Google App Password
        "imap_server": "imap.gmail.com",
        "port": 993,
        "description": "Personal Gmail"
    },
    "college": {
        "email": "26ab12@psgim.ac.in",
        "app_password": "",  # If hosted on Google Workspace / Outlook
        "imap_server": "imap.gmail.com",
        "port": 993,
        "description": "PSGIM College Webmail"
    }
}

class CollegeEmailManager:
    def __init__(self):
        self.config_path = ACCOUNTS_CONFIG_FILE
        self.accounts = self.load_accounts()

    def load_accounts(self) -> Dict:
        if not os.path.exists(self.config_path):
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_ACCOUNTS, f, indent=2)
            return DEFAULT_ACCOUNTS
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return DEFAULT_ACCOUNTS

    def save_accounts(self):
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.accounts, f, indent=2)

    def set_app_password(self, account_key: str, password: str):
        if account_key in self.accounts:
            self.accounts[account_key]["app_password"] = password.strip()
            self.save_accounts()
            return True, f"Password updated for {self.accounts[account_key]['email']}"
        return False, f"Unknown account: {account_key}"

    def check_inbox(self, account_key: str, limit: int = 5, unread_only: bool = True) -> List[Dict]:
        """Fetch latest unread emails for a specific account."""
        if account_key not in self.accounts:
            return [{"error": f"Account '{account_key}' not found."}]

        acc = self.accounts[account_key]
        user_email = acc["email"]
        password = acc["app_password"]
        imap_host = acc.get("imap_server", "imap.gmail.com")

        if not password:
            return [{
                "status": "SETUP_REQUIRED",
                "message": f"App Password missing for {user_email}. Google requires a 16-character App Password to connect securely."
            }]

        results = []
        try:
            mail = imaplib.IMAP4_SSL(imap_host, 993)
            mail.login(user_email, password)
            mail.select("INBOX")

            search_query = "UNSEEN" if unread_only else "ALL"
            res, data = mail.search(None, search_query)
            if res != "OK" or not data[0]:
                mail.close()
                mail.logout()
                return [{"status": "NO_NEW_EMAILS", "message": f"No unread emails in {user_email}."}]

            msg_ids = data[0].split()
            msg_ids = msg_ids[-limit:]
            msg_ids.reverse()

            for mid in msg_ids:
                status, msg_data = mail.fetch(mid, "(RFC822)")
                if status != "OK":
                    continue

                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)

                # Decode subject
                subject_raw = msg.get("Subject", "(No Subject)")
                decoded_parts = decode_header(subject_raw)
                subject = ""
                for part, encoding in decoded_parts:
                    if isinstance(part, bytes):
                        subject += part.decode(encoding if encoding else "utf-8", errors="ignore")
                    else:
                        subject += str(part)

                sender = msg.get("From", "Unknown")
                date = msg.get("Date", "")

                # Snippet
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            payload = part.get_payload(decode=True)
                            if payload:
                                body = payload.decode(errors="ignore")
                                break
                else:
                    payload = msg.get_payload(decode=True)
                    if payload:
                        body = payload.decode(errors="ignore")

                results.append({
                    "account": user_email,
                    "sender": sender,
                    "subject": subject,
                    "date": date,
                    "snippet": body.strip()[:180].replace("\n", " ") if body else ""
                })

            mail.close()
            mail.logout()
            return results
        except Exception as e:
            return [{"error": f"Failed connecting to {user_email}: {str(e)}"}]
