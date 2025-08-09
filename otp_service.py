import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import datetime
from flask import current_app
# --- MODIFIED: Import the database and new OTP model ---
from extensions import db
from models import OTP

# In-memory storage is no longer needed
# otp_store = {}
MAX_ATTEMPTS = 5

def generate_otp(email):
    """
    Generates a 6-digit OTP, stores it in the database, and returns it.
    """
    # Clean up any old OTP for this email first
    OTP.query.filter_by(email=email).delete()

    otp_code = str(random.randint(100000, 999999))
    new_otp = OTP(email=email, otp=otp_code)
    db.session.add(new_otp)
    db.session.commit()
    print(f"Generated OTP for {email}: {otp_code}") # For debugging
    return otp_code

def send_otp_email(recipient_email, otp):
    """
    Sends an email to the user with their OTP. (No changes needed here)
    """
    try:
        msg = MIMEMultipart()
        msg['From'] = current_app.config['MAIL_DEFAULT_SENDER'][1]
        msg['To'] = recipient_email
        msg['Subject'] = 'Your Verification Code for Question Bank'

        body = f"""
        Hello,

        Thank you for using Question Bank.
        Your One-Time Password (OTP) is: {otp}

        This code is valid for 5 minutes.

        If you did not request this, please ignore this email.

        Best regards,
        The Question Bank Team
        """
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(current_app.config['MAIL_SERVER'], current_app.config['MAIL_PORT'])
        server.starttls()
        server.login(current_app.config['MAIL_USERNAME'], current_app.config['MAIL_PASSWORD'])
        text = msg.as_string()
        server.sendmail(current_app.config['MAIL_DEFAULT_SENDER'][1], recipient_email, text)
        server.quit()
        return True
    except Exception as e:
        print(f"Error sending OTP email to {recipient_email}: {e}")
        return False

def verify_otp(email, user_otp):
    """
    Verifies the OTP from the database, checking for expiry and attempt limits.
    """
    stored_otp_data = OTP.query.filter_by(email=email).first()

    if not stored_otp_data:
        return False, "OTP not found or has expired. Please request a new one."

    # Check if OTP has expired (5-minute validity)
    if datetime.datetime.utcnow() - stored_otp_data.timestamp > datetime.timedelta(minutes=5):
        db.session.delete(stored_otp_data)
        db.session.commit()
        return False, "OTP has expired. Please request a new one."

    # Increment and check attempt counter
    stored_otp_data.attempts += 1
    if stored_otp_data.attempts > MAX_ATTEMPTS:
        db.session.delete(stored_otp_data)
        db.session.commit()
        return False, f"Maximum of {MAX_ATTEMPTS} attempts reached. Please request a new OTP."

    # Check if the OTP is correct
    if user_otp == stored_otp_data.otp:
        db.session.delete(stored_otp_data) # Clean up on success
        db.session.commit()
        return True, "OTP verified successfully."
    else:
        db.session.commit() # Save the increased attempt count
        remaining_attempts = MAX_ATTEMPTS - stored_otp_data.attempts
        if remaining_attempts > 0:
            return False, f"Invalid OTP. You have {remaining_attempts} attempts remaining."
        else:
            db.session.delete(stored_otp_data)
            db.session.commit()
            return False, "Invalid OTP. No attempts remaining. Please request a new one."