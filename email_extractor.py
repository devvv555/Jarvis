"""
J.A.R.V.I.S. Email Extractor Module
Extracts emails from text, files, college documents, or directly from Gmail/IMAP.
100% Free - uses Python built-ins.
"""

import re
import os
import imaplib
import email
from email.header import decode_header
from typing import List, Dict, Optional

EMAIL_REGEX = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'

class EmailExtractor:
    def __init__(self):
        pass

    def extract_from_text(self, text: str) -> List[str]:
        """Extract all unique valid email addresses from any raw string/text."""
        found = re.findall(EMAIL_REGEX, text)
        # Deduplicate while preserving order
        unique_emails = []
        for e in found:
            clean = e.strip().lower()
            if clean not in unique_emails:
                unique_emails.append(clean)
        return unique_emails

    def extract_from_file(self, file_path: str) -> List[str]:
        """Extract emails from a local text, CSV, markdown, or log file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        return self.extract_from_text(content)

    def extract_from_inbox(
        self, 
        email_user: str, 
        email_password: str, 
        imap_server: str = "imap.gmail.com",
        folder: str = "INBOX",
        limit: int = 10,
        unread_only: bool = True
    ) -> List[Dict]:
        """
        Connect to inbox via IMAP (Gmail, Outlook, College Webmail)
        and extract recent messages, senders, subjects, dates, and email addresses.
        """
        results = []
        try:
            mail = imaplib.IMAP4_SSL(imap_server)
            mail.login(email_user, email_password)
            mail.select(folder)

            search_criteria = 'UNSEEN' if unread_only else 'ALL'
            status, messages = mail.search(None, search_criteria)
            
            if status != 'OK' or not messages[0]:
                mail.close()
                mail.logout()
                return results

            message_ids = messages[0].split()
            # Get latest first
            message_ids = message_ids[-limit:]
            message_ids.reverse()

            for msg_id in message_ids:
                res, data = mail.fetch(msg_id, '(RFC822)')
                if res != 'OK':
                    continue

                raw_email = data[0][1]
                msg = email.message_from_bytes(raw_email)

                # Decode subject
                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding if encoding else "utf-8", errors="ignore")

                # Sender
                sender = msg.get("From")
                date = msg.get("Date")

                # Extract sender email
                sender_emails = self.extract_from_text(sender) if sender else []
                sender_email = sender_emails[0] if sender_emails else sender

                # Extract body
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        content_disposition = str(part.get("Content-Disposition"))
                        if content_type == "text/plain" and "attachment" not in content_disposition:
                            payload = part.get_payload(decode=True)
                            if payload:
                                body = payload.decode(errors="ignore")
                                break
                else:
                    payload = msg.get_payload(decode=True)
                    if payload:
                        body = payload.decode(errors="ignore")

                # Extract any emails mentioned in the body
                body_emails = self.extract_from_text(body)

                results.append({
                    "id": msg_id.decode(),
                    "sender": sender,
                    "sender_email": sender_email,
                    "subject": subject,
                    "date": date,
                    "body_snippet": body.strip()[:200] if body else "",
                    "extracted_emails_in_body": body_emails
                })

            mail.close()
            mail.logout()
            return results
        except Exception as e:
            return [{"error": str(e)}]
