import csv
import os
from email.mime.base import MIMEBase
from email import encoders

def read_csv(file_path):
    """Reads a CSV file and extracts recipient details."""
    recipients = []
    try:
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                recipients.append({
                    "name": row.get("name"),
                    "email": row.get("email"),
                    "job_role": row.get("job_role"),
                    "company_name": row.get("company_name"),
                    "company_website": row.get("company_website", "").strip(),
                    "company_context": row.get("company_context", "").strip(),
                })
        return recipients
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return []

def attach_file(msg, file_path):
    """Attaches the resume to the email."""
    try:
        with open(file_path, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(file_path)}")
            msg.attach(part)
    except Exception as e:
        print(f"Error attaching resume: {e}")
