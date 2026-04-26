# pages/email_utils.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.conf import settings

def send_custom_email(subject, body, to_email):
    """Send email using your custom domain SMTP"""
    try:
        msg = MIMEMultipart()
        msg['From'] = settings.EMAIL_HOST_USER
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        # Connect using SSL or TLS based on settings
        if settings.EMAIL_USE_SSL:
            server = smtplib.SMTP_SSL(settings.EMAIL_HOST, settings.EMAIL_PORT)
        else:
            server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
            if settings.EMAIL_USE_TLS:
                server.starttls()
        
        server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        print(f" Email sent to {to_email}")
        return True
    except Exception as e:
        print(f" Email failed: {e}")
        return False

def send_contract_notification(contract):
    """Send contract notification email to admin"""
    subject = f'New Contract Agreement - {contract.full_name}'
    
    # Plain text version
    body = f"""
    New Contract Agreement Submitted
    
    ========================================
    
    PERSONAL INFORMATION:
    - Name: {contract.full_name}
    - Email: {contract.email}
    - Phone: {contract.phone}
    
    ADDRESS:
    - {contract.street_address}
    - {contract.address_line2 if contract.address_line2 else 'N/A'}
    - {contract.city}, {contract.state_region} {contract.postal_code}
    - {contract.country}
    
    CONTRACT DETAILS:
    - Start Date: {contract.contract_duration.strftime('%B %Y') if contract.contract_duration else 'Not set'}
    - Payment Methods: {', '.join([m.name for m in contract.payment_methods.all()]) if contract.payment_methods.all() else 'Not selected'}
    - Bank Name: {contract.bank_name or 'Not provided'}
    
    AGREEMENT TERMS:
    - Agree to post and promote: {'Yes' if contract.agree_to_promote else 'No'}
    - Agree to post twice weekly: {'Yes' if contract.agree_to_post_twice else 'No'}
    
    SIGNATURE:
    - Signed by: {contract.signature}
    - Date: {contract.created_at.strftime('%Y-%m-%d %H:%M:%S') if contract.created_at else 'Just now'}
    - IP Address: {contract.ip_address or 'Not recorded'}
    
    ========================================
    View in admin: /admin/pages/contractagreement/{contract.id}/change/
    """
    
    return send_custom_email(subject, body, settings.ADMIN_EMAIL)