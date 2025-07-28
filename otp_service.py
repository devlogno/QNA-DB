# otp_service.py
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import datetime
from flask import current_app

# In-memory storage for OTPs. For production, consider using Redis or a database.
otp_store = {}
MAX_ATTEMPTS = 5

def generate_otp(email):
    """
    Generates a 6-digit OTP, stores it with a timestamp and attempt counter, and returns it.
    """
    otp = str(random.randint(100000, 999999))
    timestamp = datetime.datetime.now()
    # Storing OTP with timestamp and an attempt counter
    otp_store[email] = {'otp': otp, 'timestamp': timestamp, 'attempts': 0}
    print(f"Generated OTP for {email}: {otp}") # For debugging purposes
    return otp

def send_otp_email(recipient_email, otp):
    """
    Sends an email to the user with their OTP.
    """
    try:
        msg = MIMEMultipart()
        msg['From'] = current_app.config['MAIL_DEFAULT_SENDER'][1]
        msg['To'] = recipient_email
        msg['Subject'] = 'Your Verification Code for Question Bank'

        # UPDATED: Changed validity time in the email body
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
        print(f"Error sending OTP email to {recipient_email}: {e}") # Log the error
        return False

def verify_otp(email, user_otp):
    """
    Verifies the OTP provided by the user, checking for expiry and attempt limits.
    """
    if email not in otp_store:
        return False, "OTP not found or has expired. Please request a new one."

    stored_data = otp_store[email]
    stored_otp = stored_data['otp']
    timestamp = stored_data['timestamp']

    # UPDATED: Check if OTP has expired (5-minute validity)
    if datetime.datetime.now() - timestamp > datetime.timedelta(minutes=5):
        del otp_store[email] # Clean up expired OTP
        return False, "OTP has expired. Please request a new one."

    # Increment attempt counter
    stored_data['attempts'] += 1

    # Check if attempts have exceeded the maximum
    if stored_data['attempts'] > MAX_ATTEMPTS:
        del otp_store[email] # Clean up after too many attempts
        return False, f"Maximum of {MAX_ATTEMPTS} attempts reached. Please request a new OTP."

    # Check if the OTP is correct
    if user_otp == stored_otp:
        del otp_store[email] # Clean up successfully used OTP
        return True, "OTP verified successfully."
    else:
        remaining_attempts = MAX_ATTEMPTS - stored_data['attempts']
        if remaining_attempts > 0:
            # Provide feedback on remaining attempts
            return False, f"Invalid OTP. You have {remaining_attempts} attempts remaining."
        else:
            # Final attempt failed
            del otp_store[email]
            return False, "Invalid OTP. No attempts remaining. Please request a new one."
