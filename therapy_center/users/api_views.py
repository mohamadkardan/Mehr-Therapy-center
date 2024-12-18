from datetime import timedelta
import pyotp
import json
from django.utils.timezone import now
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import User, Client, Therapist, OneTimePassword
import hashlib
from decouple import config
import base64
from cryptography.fernet import Fernet
import requests

OTP_REQUEST_LIMIT = 5
OTP_REQUEST_COUNT_TIMEOUT = 30 # In seconds

SMS_IR_URL = "https://api.sms.ir/v1/send/verify"
SMS_TEMPLATE_ID = 238824
SMS_SUCCESSFULLY_SENT = "موفق"

KEY_PHONE_NUMBER = 'phone_number'
KEY_SECRET_SALT = 'SECRET_SALT'
KEY_OTP = 'otp'
KEY_MESSAGE = 'message'
KEY_NAME = 'name'
KEY_VALUE = 'value'

# Load the encryption key from environment variables
ENCRYPTION_KEY = config("ENCRYPTION_KEY").encode()
cipher_suite = Fernet(ENCRYPTION_KEY)

def encrypt_otp(otp):
    """Encrypt the OTP before storing it in the database."""
    return cipher_suite.encrypt(otp.encode()).decode()

def decrypt_otp(encrypted_otp):
    """Decrypt the OTP when retrieving it from the database."""
    return cipher_suite.decrypt(encrypted_otp.encode()).decode()

def is_user_exists(phone_number):
    is_exists = User.objects.filter(phone_number=phone_number).exists()
    if is_exists:
        return True
    else:
        return False

def generate_otp(user):
    secret_salt = config(KEY_SECRET_SALT)
    raw_key = f"{user.phone_number}_{secret_salt}_{now()}"
    hashed_key = hashlib.sha256(raw_key.encode()).digest()
    user_secret = base64.b32encode(hashed_key).decode('utf-8')

    # Generate OTP
    totp = pyotp.TOTP(user_secret, interval=120)  # 6-digit OTP
    otp = totp.now()
    encrypted_otp = encrypt_otp(otp)
    print('raw otp: ' + otp)

    return encrypted_otp

def store_otp(encrypted_otp, user):
    exists_one_time_password = OneTimePassword.objects.filter(user=user).exists()
    if exists_one_time_password:
        stored_otp = OneTimePassword.objects.get(user=user)
        stored_otp.value = encrypted_otp
        stored_otp.expire_time = now() + timedelta(minutes=2)
        stored_otp.save()
    else:
        OneTimePassword.objects.create(value=encrypted_otp, user=user, expire_time=now() + timedelta(minutes=2))

def send_otp_with_smsir(phone_number, template_id, parameters, api_key):
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'text/plain',
            'x-api-key': api_key
        }
        payload = {
            "mobile": phone_number,
            "templateId": template_id,
            "parameters": parameters
        }

        try:
            response = requests.post(SMS_IR_URL, headers=headers, data=json.dumps(payload))
            response.raise_for_status()  # بررسی وضعیت پاسخ
            return response.json()
        except requests.exceptions.RequestException as e:
            return {KEY_MESSAGE: str(e)}

@api_view(['POST'])
def request_otp(request):
    data = json.loads(request.body)
    phone_number = data.get(KEY_PHONE_NUMBER)

    if not phone_number:
        return Response({KEY_MESSAGE: 'Phone number is required.'}, status=status.HTTP_400_BAD_REQUEST)
    else:
        if not phone_number.isnumeric():
            return Response({KEY_MESSAGE: 'Phone number is invalid'}, status=status.HTTP_400_BAD_REQUEST)

        if len(phone_number) > 11:
            return Response({KEY_MESSAGE: 'Phone number is too long'}, status=status.HTTP_400_BAD_REQUEST)

    if not is_user_exists(phone_number):
        user = User.objects.create(phone_number=phone_number)
    else:
        user = User.objects.filter(phone_number=phone_number).first()

    encrypted_otp = generate_otp(user)
    store_otp(encrypted_otp,user)

    otp_response = send_otp_with_smsir(
        phone_number=phone_number,
        template_id=SMS_TEMPLATE_ID,
        parameters= get_otp_sms_parameters(decrypt_otp(encrypted_otp)),
        api_key= config("SMS_IR_API_KEY")
    )

    if otp_response:
       otp_response_message = otp_response.get(KEY_MESSAGE)
       if otp_response_message == SMS_SUCCESSFULLY_SENT:
            return Response({KEY_MESSAGE: "OTP sent successfully!"}, status=status.HTTP_200_OK)

def get_otp_sms_parameters(otp):
    return [{KEY_NAME: "otp", KEY_VALUE: otp}]

@api_view(['POST'])
def verify_otp(request):
    data = json.loads(request.body)
    phone_number = data.get(KEY_PHONE_NUMBER)
    input_otp = data.get(KEY_OTP)

    if not is_user_exists(phone_number):
       return Response({KEY_MESSAGE: 'Registration is required. Phone number is not registered.'}, status=status.HTTP_400_BAD_REQUEST)
    else:
        if len(input_otp) != 6:
            return Response({KEY_MESSAGE: 'OTP is invalid'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            try:
                user = User.objects.get(phone_number=phone_number)
                one_time_password = OneTimePassword.objects.get(user=user)
            except OneTimePassword.DoesNotExist:
                return Response({KEY_MESSAGE: 'User hasn\'t OTP'}, status=status.HTTP_400_BAD_REQUEST)
            except User.DoesNotExist:
                return Response({KEY_MESSAGE: 'User is not registered'}, status=status.HTTP_400_BAD_REQUEST)

            stored_otp = decrypt_otp(one_time_password.value)
            if input_otp == stored_otp:
                if one_time_password.is_expired():
                    one_time_password.delete()
                    return Response({KEY_MESSAGE: 'OTP expired'}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    one_time_password.delete()
                    return Response({KEY_MESSAGE: 'OTP verified successfully'}, status=status.HTTP_200_OK)
            else:
                return Response({KEY_MESSAGE: 'OTP is Invalid'}, status=status.HTTP_400_BAD_REQUEST)