from sib_api_v3_sdk import Configuration, ApiClient, TransactionalEmailsApi, SendSmtpEmail
from sib_api_v3_sdk.rest import ApiException
from pprint import pprint
import os

# Configure the API key for Brevo
#
api_key = os.getenv("BREVO_API_KEY")
if not api_key:
    raise ValueError("API Key is missing. Set the BREVO_API_KEY environment variable.")

# Configure Brevo API
configuration = Configuration()
configuration.api_key['api-key'] = api_key

# Create API client instance
api_instance = TransactionalEmailsApi(ApiClient(configuration))


def send_email_inquirey(email,bname, fname, lname, pnumber):
    send = "Kyej2005@gmail.com"
    """
    Sends an email using the Brevo API.

    Args:
        send (str): Recipient's email address.
        bname (str): Business name or subject line for the email.
        fname (str): First name of the recipient.
        lname (str): Last name of the recipient.
        pnumber (str): Contact phone number.

    Returns:
        dict: Response from Brevo API or error message.
    """
    subject = f"New Business: {bname}!"
    html_content = f"""
    <html>
        <body>
            <h1>Yo new Potiential client boss! {bname}!</h1>
            <p>Hi meet, {fname} {lname}</p>
            <p>You can contact them at: </p>
            <p>Phone: {pnumber}</b>.</p>
            <p>Email: {email}
            <p>Goodluck Mr bossman</p>
        </body>
    </html>
    """

    # Define the email
    email = SendSmtpEmail(
        sender={"name": "Thrive Services", "email": "no-reply@thrivemailing.com"},
        to=[{"email": send, "name": f"{fname} {lname}"}],
        subject=subject,
        html_content=html_content
    )

    # Send the email
    try:
        api_response = api_instance.send_transac_email(email)
        pprint(api_response)
        return {"status": "success", "response": api_response}
    except ApiException as e:
        print(f"Exception when sending email: {e}")
        return {"status": "error", "message": str(e)}
    
    
def reset_password_code(email, fname, lname, code):
    """
    Sends an email using the Brevo API.

    Args:
        send (str): Recipient's email address.
        bname (str): Business name or subject line for the email.
        fname (str): First name of the recipient.
        lname (str): Last name of the recipient.
        pnumber (str): Contact phone number.

    Returns:
        dict: Response from Brevo API or error message.
    """
    subject = f"Code password for Reset: {code}!"
    html_content = f"""
    <html>
        <body>
            <h1>Reset your password with this code: {code}!</h1>
            <p>Thanks {fname} {lname} for using our platform!</p>
            <p>Big thanks from us!</p>
        </body>
    </html>
    """

    # Define the email
    email = SendSmtpEmail(
        sender={"name": "Thrive Services", "email": "no-reply@thrivemailing.com"},
        to=[{"email": email, "name": f"{fname} {lname}"}],
        subject=subject,
        html_content=html_content
    )

    # Send the email
    try:
        api_response = api_instance.send_transac_email(email)
        pprint(api_response)
        return {"status": "success", "response": api_response}
    except ApiException as e:
        print(f"Exception when sending email: {e}")
        return {"status": "error", "message": str(e)}




def contact_email(email, fname, lname, message):
    send = "Kyej2005@gmail.com"

    subject = "InuConnect Contact Message!"
    html_content = f"""
    <html>
        <body>
            <h1>Message received</h1>
            <p>Hi meet, {fname} {lname}</p>
            <p>Email: {email}</p>
            <p>Message: {message}</p>
        </body>
    </html>
    """

    email_obj = SendSmtpEmail(
        sender={"name": "Thrive Services", "email": "no-reply@thrivemailing.com"},
        to=[{"email": send, "name": f"{fname} {lname}"}],
        subject=subject,
        html_content=html_content
    )

    try:
        api_response = api_instance.send_transac_email(email_obj)
        print("Email sent successfully:", api_response)
        return {"status": "success", "response": api_response}
    except ApiException as e:
        print(f"Error sending email: {repr(e)}")
        return {"status": "error", "message": repr(e)}
    
    

contact_email("kyej@kdkd.com", "fname", "lname", "message")