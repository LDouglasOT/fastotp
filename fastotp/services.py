"""
FastOTP Service Layer
=====================
Placeholder implementations for FastOTP Python client and Payment Gateway logic.
Replace the stub methods with actual SDK/API calls.
"""
import hashlib
import random
import string
import logging
from datetime import timedelta
from django.utils import timezone
from django.conf import settings

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
#  FastOTP Delivery Client
# ─────────────────────────────────────────────

class FastOTPClient:
    """
    Wrapper around the FastOTP delivery API.
    Supports WhatsApp, SMS, Voice, and Email channels.

    Usage:
        client = FastOTPClient()
        result = client.send_otp("+234801234567", channel="whatsapp")
    """

    BASE_URL = getattr(settings, 'FASTOTP_API_URL', 'https://api.fastotp.co/v1')
    API_KEY = getattr(settings, 'FASTOTP_API_KEY', '')

    def __init__(self):
        self.session_headers = {
            'Authorization': f'Bearer {self.API_KEY}',
            'Content-Type': 'application/json',
        }

    def send_otp(self, identifier: str, channel: str = 'whatsapp', length: int = 6,
                 expires_in: int = 300, sender_id: str = '') -> dict:
        """
        Send an OTP to the given identifier via the specified channel.

        Args:
            identifier: Phone number (E.164) or email address.
            channel: 'whatsapp' | 'sms' | 'email' | 'voice'
            length: Number of OTP digits (4–8).
            expires_in: Seconds until OTP expires (default: 5 min).
            sender_id: Custom sender ID for SMS.

        Returns:
            dict: {
                'success': bool,
                'otp_id': str,
                'expires_at': datetime,
                'latency_ms': int,
                'error': str | None,
            }
        """
        # TODO: Replace with real HTTP call using requests / httpx
        # import requests
        # response = requests.post(f"{self.BASE_URL}/send", json={...}, headers=self.session_headers)
        # data = response.json()

        # ── STUB ──────────────────────────────────
        logger.info(f"[STUB] Sending OTP to {identifier} via {channel}")
        otp = ''.join(random.choices(string.digits, k=length))
        return {
            'success': True,
            'otp_id': 'stub_' + identifier[:8],
            'otp': otp,          # Only for testing — never expose in prod
            'expires_at': timezone.now() + timedelta(seconds=expires_in),
            'latency_ms': random.randint(180, 900),
            'error': None,
        }

    def verify_otp(self, identifier: str, otp: str, otp_id: str = '') -> dict:
        """
        Verify a previously sent OTP.

        Returns:
            dict: {'success': bool, 'message': str}
        """
        # TODO: Replace with real verification call
        logger.info(f"[STUB] Verifying OTP for {identifier}")
        return {'success': True, 'message': 'OTP verified successfully.'}

    def get_delivery_status(self, otp_id: str) -> dict:
        """Poll delivery status for a sent OTP."""
        # TODO: Implement real polling
        return {'status': 'delivered', 'latency_ms': 420}

    def get_coverage(self) -> list:
        """Fetch list of supported countries with rates."""
        # TODO: Replace with real API call
        return COVERAGE_DATA


# ─────────────────────────────────────────────
#  Payment Gateway — Paystack
# ─────────────────────────────────────────────

class PaystackGateway:
    """
    Paystack payment integration.

    pip install paystackapi
    Set PAYSTACK_SECRET_KEY in Django settings.
    """

    SECRET_KEY = getattr(settings, 'PAYSTACK_SECRET_KEY', '')
    BASE_URL = 'https://api.paystack.co'

    def initialize_transaction(self, email: str, amount_kobo: int,
                                metadata: dict = None, callback_url: str = '') -> dict:
        """
        Initialise a Paystack transaction.

        Args:
            email: Customer's email.
            amount_kobo: Amount in kobo (NGN * 100) or pesewas (GHS * 100).
            metadata: Extra data (user_id, package_id, credits).
            callback_url: URL to redirect after payment.

        Returns:
            dict: {'authorization_url': str, 'access_code': str, 'reference': str}
        """
        # TODO:
        # from paystackapi.transaction import Transaction
        # response = Transaction.initialize(email=email, amount=amount_kobo,
        #                                   metadata=metadata, callback_url=callback_url)
        # return response['data']

        logger.info(f"[STUB] Paystack init for {email}, amount={amount_kobo}")
        return {
            'authorization_url': 'https://checkout.paystack.com/stub_access_code',
            'access_code': 'stub_access_code',
            'reference': 'stub_ref_' + email[:6],
        }

    def verify_transaction(self, reference: str) -> dict:
        """
        Verify a Paystack payment by reference.

        Returns:
            dict: {'status': 'success'|'failed', 'amount': int, 'metadata': dict}
        """
        # TODO:
        # from paystackapi.transaction import Transaction
        # response = Transaction.verify(reference)
        # return response['data']

        logger.info(f"[STUB] Verifying Paystack txn: {reference}")
        return {'status': 'success', 'amount': 100000, 'metadata': {}}


# ─────────────────────────────────────────────
#  Payment Gateway — Flutterwave
# ─────────────────────────────────────────────

class FlutterwaveGateway:
    """
    Flutterwave payment integration.

    pip install flutterwave3
    Set FLUTTERWAVE_SECRET_KEY in Django settings.
    """

    SECRET_KEY = getattr(settings, 'FLUTTERWAVE_SECRET_KEY', '')
    BASE_URL = 'https://api.flutterwave.com/v3'

    def initialize_payment(self, tx_ref: str, amount: float, currency: str,
                            customer: dict, redirect_url: str, meta: dict = None) -> dict:
        """
        Create a Flutterwave payment link.

        Args:
            tx_ref: Unique transaction reference.
            amount: Amount to charge.
            currency: 'NGN' | 'GHS' | 'KES' | 'USD' etc.
            customer: {'email': str, 'name': str, 'phone_number': str}
            redirect_url: URL to redirect after payment.
            meta: Extra metadata dict.

        Returns:
            dict: {'link': str}  — payment checkout URL
        """
        # TODO:
        # import rave_python
        # rave = rave_python.Rave(self.SECRET_KEY, production=True)
        # payload = {"txRef": tx_ref, "amount": amount, "currency": currency, ...}
        # response = rave.Card.charge(payload)

        logger.info(f"[STUB] Flutterwave payment link for {customer.get('email')}")
        return {'link': f'https://checkout.flutterwave.com/v3/hosted/pay/stub_{tx_ref}'}

    def verify_payment(self, transaction_id: str) -> dict:
        """Verify a Flutterwave payment."""
        # TODO: GET /transactions/{transaction_id}/verify
        logger.info(f"[STUB] Verifying Flutterwave txn: {transaction_id}")
        return {'status': 'successful', 'amount': 10, 'currency': 'USD'}


# ─────────────────────────────────────────────
#  OTP Business Logic
# ─────────────────────────────────────────────

def hash_otp(otp: str, identifier: str) -> str:
    """Hash an OTP before storing — never store plain OTPs."""
    salt = getattr(settings, 'SECRET_KEY', '')[:16]
    return hashlib.sha256(f"{salt}:{identifier}:{otp}".encode()).hexdigest()


def generate_registration_otp(user) -> str:
    """Generate and attach an OTP for WhatsApp signup verification."""
    from .models import OTPLog
    otp = ''.join(random.choices(string.digits, k=6))
    user.verification_otp = hash_otp(otp, user.whatsapp_number)
    user.otp_expires_at = timezone.now() + timedelta(minutes=10)
    user.save(update_fields=['verification_otp', 'otp_expires_at'])

    OTPLog.objects.create(
        user=user,
        identifier=user.whatsapp_number,
        channel='whatsapp',
        otp_hash=hash_otp(otp, user.whatsapp_number),
        status='sent',
        expires_at=user.otp_expires_at,
    )
    return otp  # Return only to show in UI for demo; remove in production


def verify_registration_otp(user, submitted_otp: str) -> bool:
    """Verify the registration OTP submitted by the user."""
    if timezone.now() > user.otp_expires_at:
        return False
    expected = hash_otp(submitted_otp, user.whatsapp_number)
    if expected == user.verification_otp:
        user.is_verified = True
        user.verification_otp = ''
        user.save(update_fields=['is_verified', 'verification_otp'])
        return True
    return False


def credit_user_account(user, credits: float, transaction) -> bool:
    """Credit a user's account after successful payment."""
    from .models import CreditBalance
    balance, _ = CreditBalance.objects.get_or_create(user=user)
    balance.balance += credits
    balance.total_topped_up += transaction.amount_usd
    balance.save()
    transaction.status = 'completed'
    transaction.save()
    return True


def debit_user_account(user, credits: float, otp_log) -> bool:
    """Debit credits when an OTP is sent."""
    from .models import CreditBalance
    balance, _ = CreditBalance.objects.get_or_create(user=user)
    if balance.balance < credits:
        return False
    balance.balance -= credits
    balance.total_consumed += credits
    balance.save()
    otp_log.cost_credits = credits
    otp_log.save()
    return True


# ─────────────────────────────────────────────
#  Static Coverage Data
# ─────────────────────────────────────────────

COVERAGE_DATA = [
    {"country": "Nigeria",       "code": "NG", "flag": "🇳🇬", "dial": "+234", "whatsapp": 99.2, "sms": 98.1, "cost": 0.0045, "currency_code": "NGN",  "currency_symbol": "₦",     "local_cost": 7.2,  "local_cost_display": "₦7.2"},
    {"country": "Kenya",         "code": "KE", "flag": "🇰🇪", "dial": "+254", "whatsapp": 98.7, "sms": 97.5, "cost": 0.0040, "currency_code": "KES",  "currency_symbol": "KSh",   "local_cost": 0.52, "local_cost_display": "KSh 0.52"},
    {"country": "South Africa",  "code": "ZA", "flag": "🇿🇦", "dial": "+27",  "whatsapp": 99.5, "sms": 99.0, "cost": 0.0050, "currency_code": "ZAR",  "currency_symbol": "R",     "local_cost": 0.09, "local_cost_display": "R 0.09"},
    {"country": "Ghana",         "code": "GH", "flag": "🇬🇭", "dial": "+233", "whatsapp": 97.8, "sms": 96.4, "cost": 0.0042, "currency_code": "GHS",  "currency_symbol": "GH₵",   "local_cost": 0.06, "local_cost_display": "GH₵ 0.06"},
    {"country": "Egypt",         "code": "EG", "flag": "🇪🇬", "dial": "+20",  "whatsapp": 98.1, "sms": 97.2, "cost": 0.0038, "currency_code": "EGP",  "currency_symbol": "E£",    "local_cost": 0.19, "local_cost_display": "E£ 0.19"},
    {"country": "Ethiopia",      "code": "ET", "flag": "🇪🇹", "dial": "+251", "whatsapp": 94.3, "sms": 93.1, "cost": 0.0055, "currency_code": "ETB",  "currency_symbol": "Br",    "local_cost": 0.31, "local_cost_display": "Br 0.31"},
    {"country": "Tanzania",      "code": "TZ", "flag": "🇹🇿", "dial": "+255", "whatsapp": 96.2, "sms": 94.8, "cost": 0.0047, "currency_code": "TZS",  "currency_symbol": "TSh",   "local_cost": 12,   "local_cost_display": "TSh 12"},
    {"country": "Uganda",        "code": "UG", "flag": "🇺🇬", "dial": "+256", "whatsapp": 95.8, "sms": 94.2, "cost": 0.0046, "currency_code": "UGX",  "currency_symbol": "UGX",   "local_cost": 30,   "local_cost_display": "30 UGX"},
    {"country": "Senegal",       "code": "SN", "flag": "🇸🇳", "dial": "+221", "whatsapp": 96.5, "sms": 95.1, "cost": 0.0048, "currency_code": "XOF",  "currency_symbol": "CFA",   "local_cost": 3,    "local_cost_display": "3 CFA"},
    {"country": "Côte d'Ivoire", "code": "CI", "flag": "🇨🇮", "dial": "+225", "whatsapp": 95.9, "sms": 94.7, "cost": 0.0049, "currency_code": "XOF",  "currency_symbol": "CFA",   "local_cost": 3,    "local_cost_display": "3 CFA"},
    {"country": "Cameroon",      "code": "CM", "flag": "🇨🇲", "dial": "+237", "whatsapp": 94.7, "sms": 93.5, "cost": 0.0052, "currency_code": "XAF",  "currency_symbol": "FCFA",  "local_cost": 3.2,  "local_cost_display": "3.2 FCFA"},
    {"country": "Zambia",        "code": "ZM", "flag": "🇿🇲", "dial": "+260", "whatsapp": 93.4, "sms": 92.0, "cost": 0.0054, "currency_code": "ZMW",  "currency_symbol": "ZK",    "local_cost": 0.14, "local_cost_display": "ZK 0.14"},
    {"country": "Rwanda",        "code": "RW", "flag": "🇷🇼", "dial": "+250", "whatsapp": 96.8, "sms": 95.6, "cost": 0.0043, "currency_code": "RWF",  "currency_symbol": "RF",    "local_cost": 5.9,  "local_cost_display": "RF 5.9"},
    {"country": "Morocco",       "code": "MA", "flag": "🇲🇦", "dial": "+212", "whatsapp": 97.5, "sms": 96.3, "cost": 0.0041, "currency_code": "MAD",  "currency_symbol": "د.م.",  "local_cost": 0.04, "local_cost_display": "0.04 MAD"},
    {"country": "Tunisia",       "code": "TN", "flag": "🇹🇳", "dial": "+216", "whatsapp": 97.1, "sms": 95.9, "cost": 0.0042, "currency_code": "TND",  "currency_symbol": "د.ت",   "local_cost": 0.013,"local_cost_display": "0.013 TND"},
    {"country": "Zimbabwe",      "code": "ZW", "flag": "🇿🇼", "dial": "+263", "whatsapp": 92.1, "sms": 90.8, "cost": 0.0058, "currency_code": "USD",  "currency_symbol": "$",     "local_cost": 0.006,"local_cost_display": "$0.006"},
    {"country": "Mozambique",    "code": "MZ", "flag": "🇲🇿", "dial": "+258", "whatsapp": 91.5, "sms": 90.2, "cost": 0.0060, "currency_code": "MZN",  "currency_symbol": "MT",    "local_cost": 0.38, "local_cost_display": "MT 0.38"},
    {"country": "Angola",        "code": "AO", "flag": "🇦🇴", "dial": "+244", "whatsapp": 93.2, "sms": 91.9, "cost": 0.0055, "currency_code": "AOA",  "currency_symbol": "Kz",    "local_cost": 5,    "local_cost_display": "Kz 5"},
    {"country": "Botswana",      "code": "BW", "flag": "🇧🇼", "dial": "+267", "whatsapp": 95.3, "sms": 94.1, "cost": 0.0048, "currency_code": "BWP",  "currency_symbol": "P",     "local_cost": 0.07, "local_cost_display": "P 0.07"},
    {"country": "Namibia",       "code": "NA", "flag": "🇳🇦", "dial": "+264", "whatsapp": 95.0, "sms": 93.8, "cost": 0.0050, "currency_code": "NAD",  "currency_symbol": "N$",    "local_cost": 0.09, "local_cost_display": "N$ 0.09"},
    {"country": "Malawi",        "code": "MW", "flag": "🇲🇼", "dial": "+265", "whatsapp": 90.8, "sms": 89.5, "cost": 0.0062, "currency_code": "MWK",  "currency_symbol": "MK",    "local_cost": 10.7, "local_cost_display": "MK 10.7"},
    {"country": "Mali",          "code": "ML", "flag": "🇲🇱", "dial": "+223", "whatsapp": 89.3, "sms": 88.1, "cost": 0.0065, "currency_code": "XOF",  "currency_symbol": "CFA",   "local_cost": 4,    "local_cost_display": "4 CFA"},
    {"country": "Burkina Faso",  "code": "BF", "flag": "🇧🇫", "dial": "+226", "whatsapp": 88.7, "sms": 87.4, "cost": 0.0068, "currency_code": "XOF",  "currency_symbol": "CFA",   "local_cost": 4.2,  "local_cost_display": "4.2 CFA"},
    {"country": "Sierra Leone",  "code": "SL", "flag": "🇸🇱", "dial": "+232", "whatsapp": 87.2, "sms": 86.0, "cost": 0.0070, "currency_code": "SLE",  "currency_symbol": "Le",    "local_cost": 0.15, "local_cost_display": "Le 0.15"},
]
