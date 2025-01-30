import csv
import os
from email.mime.text import MIMEText
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
                    "company_name": row.get("company_name")
                })
        return recipients
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return []

def generate_email_content(name, job_role, company_name):
    """Generates email subject and body."""
    subject = f"Application for {job_role} Position at {company_name}"
    body = f"""
    Hi {name},

    I hope you're doing well.

    I am writing to express my interest in the {job_role} position at {company_name}. I believe my skills align perfectly with the role.

    Currently, I am working as a ----- at -----, and I am looking for a new challenge. I would love to connect and discuss how my expertise can contribute to your team.

    I have attached my resume for your review and look forward to hearing from you.

    Best regards,  
    Shivam Kumar
    """
    return subject, body

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
