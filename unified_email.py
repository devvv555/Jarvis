"""
J.A.R.V.I.S. Unified Email Extractor & Intelligence Engine
Monitors Personal + PSGIM College emails, categorizes them, extracts important contacts,
and fires guaranteed Windows alert popups for college circulars and urgent notices.
"""

import sys
import os
import imaplib
import email
from email.header import decode_header
from typing import List, Dict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from notifications import NotificationManager
from email_extractor import EmailExtractor

notifier = NotificationManager("J.A.R.V.I.S.")
extractor = EmailExtractor()

PERSONAL_EMAIL = "devdarshanv2005@gmail.com"
APP_PASSWORD = "ukecawxwuoskejum"
COLLEGE_TAG = "psgim.ac.in"

def fetch_and_categorize_emails(limit: int = 6):
    print(f"\n=======================================================")
    print(f"J.A.R.V.I.S. Scanning Unified Inbox: {PERSONAL_EMAIL}")
    print(f"=======================================================")

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        mail.login(PERSONAL_EMAIL, APP_PASSWORD)
        mail.select("INBOX")

        status, data = mail.search(None, "UNSEEN")
        if status != "OK" or not data[0]:
            print("Inbox up to date: No new unread messages.")
            mail.logout()
            return []

        msg_ids = data[0].split()[-limit:]
        msg_ids.reverse()

        print(f"Processing {len(msg_ids)} recent unread message(s):\n")
        processed = []

        for idx, mid in enumerate(msg_ids, 1):
            res, fetch_data = mail.fetch(mid, "(RFC822)")
            if res != "OK":
                continue
            
            raw_msg = email.message_from_bytes(fetch_data[0][1])

            # Decode Subject
            sub_raw = raw_msg.get("Subject", "(No Subject)")
            decoded = decode_header(sub_raw)
            subject = ""
            for part, enc in decoded:
                if isinstance(part, bytes):
                    subject += part.decode(enc if enc else "utf-8", errors="ignore")
                else:
                    subject += str(part)

            sender = raw_msg.get("From", "Unknown Sender")
            date = raw_msg.get("Date", "")

            # Extract body
            body = ""
            if raw_msg.is_multipart():
                for part in raw_msg.walk():
                    if part.get_content_type() == "text/plain":
                        payload = part.get_payload(decode=True)
                        if payload:
                            body = payload.decode(errors="ignore")
                            break
            else:
                payload = raw_msg.get_payload(decode=True)
                if payload:
                    body = payload.decode(errors="ignore")

            # Check if this email originated from or mentions PSGIM
            is_college = COLLEGE_TAG in sender.lower() or COLLEGE_TAG in body.lower() or "psg" in subject.lower()

            # Extract all emails referenced in body
            referenced_emails = extractor.extract_from_text(body)

            badge = "[COLLEGE / PSGIM]" if is_college else "[PERSONAL]"
            print(f"{badge} [{idx}]")
            print(f"  • From:    {sender}")
            print(f"  • Subject: {subject.strip()}")
            if referenced_emails:
                print(f"  • Extracted Contacts: {', '.join(referenced_emails[:3])}")
            print("-" * 55)

            # Fire priority desktop alert for college emails or latest email
            if is_college and idx <= 2:
                notifier.notify("PSGIM College Notice", f"Subject: {subject[:80]}\nFrom: {sender}")
            elif idx == 1:
                notifier.notify("New Unread Email", f"From: {sender.split('<')[0]}\nSubject: {subject[:70]}")

            processed.append({
                "category": "college" if is_college else "personal",
                "sender": sender,
                "subject": subject,
                "date": date,
                "contacts": referenced_emails
            })

        mail.logout()
        return processed
    except Exception as e:
        print(f"Error checking unified inbox: {e}")
        return []

if __name__ == "__main__":
    fetch_and_categorize_emails()
