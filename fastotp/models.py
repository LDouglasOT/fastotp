import uuid
import secrets
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone_number = models.CharField(max_length=20, blank=True)
    whatsapp_number = models.CharField(max_length=20, blank=True)
    company_name = models.CharField(max_length=150, blank=True)
    is_verified = models.BooleanField(default=False)
    verification_otp = models.CharField(max_length=6, blank=True)
    otp_expires_at = models.DateTimeField(null=True, blank=True)
    avatar_initials = models.CharField(max_length=3, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.avatar_initials:
            fn = self.first_name[:1] if self.first_name else ''
            ln = self.last_name[:1] if self.last_name else ''
            self.avatar_initials = (fn + ln).upper() or self.username[:2].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email or self.username


class APIKey(models.Model):
    KEY_STATUS = [('active', 'Active'), ('revoked', 'Revoked')]
    KEY_ENV = [('live', 'Live'), ('test', 'Test')]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_keys')
    name = models.CharField(max_length=100, default='Default Key')
    key = models.CharField(max_length=64, unique=True)
    prefix = models.CharField(max_length=8, blank=True)
    environment = models.CharField(max_length=10, choices=KEY_ENV, default='test')
    status = models.CharField(max_length=10, choices=KEY_STATUS, default='active')
    last_used_at = models.DateTimeField(null=True, blank=True)
    total_requests = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = f"fotk_{self.environment}_{secrets.token_urlsafe(32)}"
            self.prefix = self.key[:12] + '...'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.prefix})"


class CreditBalance(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='credit_balance')
    balance = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    total_topped_up = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_consumed = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} — {self.balance} credits"


class CreditPackage(models.Model):
    TIER = [('starter', 'Starter'), ('pro', 'Pro'), ('enterprise', 'Enterprise'), ('custom', 'Custom')]

    name = models.CharField(max_length=50)
    tier = models.CharField(max_length=20, choices=TIER, default='starter')
    credits = models.PositiveIntegerField()
    price_usd = models.DecimalField(max_digits=10, decimal_places=2)
    price_per_otp = models.DecimalField(max_digits=8, decimal_places=4)
    is_popular = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    features = models.JSONField(default=list)

    class Meta:
        ordering = ['price_usd']

    def __str__(self):
        return f"{self.name} — {self.credits} credits"


class Transaction(models.Model):
    TX_TYPE = [('topup', 'Top-Up'), ('consumption', 'OTP Send'), ('refund', 'Refund')]
    TX_STATUS = [('pending', 'Pending'), ('completed', 'Completed'), ('failed', 'Failed')]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=15, choices=TX_TYPE)
    amount_usd = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    credits = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    status = models.CharField(max_length=10, choices=TX_STATUS, default='pending')
    gateway = models.CharField(max_length=50, blank=True)  # paystack / flutterwave
    gateway_ref = models.CharField(max_length=100, blank=True)
    package = models.ForeignKey(CreditPackage, null=True, blank=True, on_delete=models.SET_NULL)
    description = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.transaction_type} — {self.credits} credits — {self.status}"


class OTPLog(models.Model):
    CHANNEL = [('whatsapp', 'WhatsApp'), ('sms', 'SMS'), ('email', 'Email'), ('voice', 'Voice')]
    STATUS = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('verified', 'Verified'),
        ('failed', 'Failed'),
        ('expired', 'Expired'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otp_logs')
    api_key = models.ForeignKey(APIKey, null=True, blank=True, on_delete=models.SET_NULL)
    identifier = models.CharField(max_length=100)  # phone/email
    channel = models.CharField(max_length=15, choices=CHANNEL, default='whatsapp')
    country_code = models.CharField(max_length=5, blank=True)
    country_name = models.CharField(max_length=60, blank=True)
    otp_hash = models.CharField(max_length=128, blank=True)  # hashed OTP
    status = models.CharField(max_length=15, choices=STATUS, default='pending')
    latency_ms = models.PositiveIntegerField(null=True, blank=True)
    cost_credits = models.DecimalField(max_digits=8, decimal_places=4, default=0)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.identifier} — {self.channel} — {self.status}"


class LoginSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_sessions')
    session_key = models.CharField(max_length=40)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    device_type = models.CharField(max_length=50, blank=True)
    location = models.CharField(max_length=100, blank=True)
    is_current = models.BooleanField(default=False)
    last_active = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-last_active']

    def __str__(self):
        return f"{self.user.email} — {self.ip_address}"
