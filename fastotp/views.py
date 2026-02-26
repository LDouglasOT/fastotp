import json
import uuid
import random
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import TemplateView, ListView
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.db.models import Sum, Count, Avg
from django.db import transaction

from .models import User, APIKey, CreditBalance, CreditPackage, Transaction, OTPLog, LoginSession
from .services import (
    FastOTPClient, PaystackGateway, FlutterwaveGateway,
    generate_registration_otp, verify_registration_otp,
    credit_user_account, COVERAGE_DATA
)


# ─────────────────────────────────────────────
#  Marketing / Public Views
# ─────────────────────────────────────────────

class HomeView(TemplateView):
    template_name = 'fastotp/home.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['coverage_count'] = len(COVERAGE_DATA)
        ctx['stats'] = {
            'otps_sent': '12.4M+',
            'countries': '24+',
            'avg_latency': '380ms',
            'uptime': '99.99%',
        }
        return ctx


class CoverageView(TemplateView):
    template_name = 'fastotp/coverage.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['countries'] = COVERAGE_DATA
        return ctx


class PrivacyView(TemplateView):
    template_name = 'fastotp/privacy.html'


class TermsView(TemplateView):
    template_name = 'fastotp/terms.html'


# ─────────────────────────────────────────────
#  Auth Views
# ─────────────────────────────────────────────

class SignupStep1View(View):
    """Step 1: Collect account details."""
    template_name = 'fastotp/signup_step1.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return render(request, self.template_name)

    def post(self, request):
        data = request.POST
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        password2 = data.get('password2', '')
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        company = data.get('company_name', '').strip()
        whatsapp = data.get('whatsapp_number', '').strip()

        errors = {}
        if not email:
            errors['email'] = 'Email is required.'
        elif User.objects.filter(email=email).exists():
            errors['email'] = 'This email is already registered.'
        if len(password) < 8:
            errors['password'] = 'Password must be at least 8 characters.'
        if password != password2:
            errors['password2'] = 'Passwords do not match.'
        if not whatsapp:
            errors['whatsapp_number'] = 'WhatsApp number is required for verification.'

        if errors:
            return render(request, self.template_name, {'errors': errors, 'form': data})

        # Temporarily store in session
        request.session['signup_data'] = {
            'email': email, 'password': password,
            'first_name': first_name, 'last_name': last_name,
            'company_name': company, 'whatsapp_number': whatsapp,
        }
        return redirect('signup_step2')


class SignupStep2View(View):
    """Step 2: WhatsApp OTP Verification."""
    template_name = 'fastotp/signup_step2.html'

    def get(self, request):
        if 'signup_data' not in request.session:
            return redirect('signup')
        return render(request, self.template_name, {
            'whatsapp': request.session['signup_data'].get('whatsapp_number')
        })

    def post(self, request):
        """Final form submission after OTP verified via HTMX."""
        if 'signup_data' not in request.session:
            return redirect('signup')
        return render(request, self.template_name, {
            'whatsapp': request.session['signup_data'].get('whatsapp_number'),
            'error': 'Please verify your WhatsApp number first.'
        })


class SendSignupOTPView(View):
    """HTMX: Send OTP to WhatsApp and return OTP input fragment."""

    def post(self, request):
        signup_data = request.session.get('signup_data', {})
        whatsapp = signup_data.get('whatsapp_number', '')
        if not whatsapp:
            return HttpResponse('<p class="text-red-400">Session expired. Please restart.</p>')

        # Create temp user or retrieve pending
        user, created = User.objects.get_or_create(
            email=signup_data['email'],
            defaults={
                'username': signup_data['email'],
                'first_name': signup_data['first_name'],
                'last_name': signup_data['last_name'],
                'company_name': signup_data['company_name'],
                'whatsapp_number': whatsapp,
                'is_active': False,
            }
        )
        if created:
            user.set_password(signup_data['password'])
            user.save()
            CreditBalance.objects.create(user=user, balance=5)  # Free trial credits

        otp = generate_registration_otp(user)
        request.session['pending_user_id'] = str(user.id)

        # Return the OTP input fragment (HTMX swap)
        expires_at = (timezone.now() + timedelta(minutes=10)).isoformat()
        return render(request, 'fastotp/partials/otp_input.html', {
            'whatsapp': whatsapp,
            'demo_otp': otp,  # For demo only — remove in production
            'expires_seconds': 600,
        })


class VerifySignupOTPView(View):
    """HTMX: Verify the submitted OTP."""

    def post(self, request):
        user_id = request.session.get('pending_user_id')
        if not user_id:
            return HttpResponse('<p class="text-red-400">Session expired.</p>')

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return HttpResponse('<p class="text-red-400">User not found.</p>')

        otp_digits = [request.POST.get(f'd{i}', '') for i in range(1, 7)]
        submitted_otp = ''.join(otp_digits)

        if verify_registration_otp(user, submitted_otp):
            user.is_active = True
            user.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return render(request, 'fastotp/partials/otp_success.html', {'user': user})
        else:
            return render(request, 'fastotp/partials/otp_error.html', {
                'message': 'Invalid or expired OTP. Please try again.'
            })


class LoginView(View):
    template_name = 'fastotp/login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return render(request, self.template_name)

    def post(self, request):
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        user = authenticate(request, username=email, password=password)
        if user:
            login(request, user)
            # Track session
            LoginSession.objects.create(
                user=user,
                session_key=request.session.session_key or '',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                is_current=True,
            )
            return redirect('dashboard')
        return render(request, self.template_name, {
            'error': 'Invalid email or password.',
            'email': email,
        })


class LogoutView(LoginRequiredMixin, View):
    def post(self, request):
        logout(request)
        return redirect('home')


# ─────────────────────────────────────────────
#  Dashboard Views
# ─────────────────────────────────────────────

class DashboardView(LoginRequiredMixin, TemplateView):
    login_url = 'login'
    template_name = 'fastotp/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        balance, _ = CreditBalance.objects.get_or_create(user=user)
        recent_logs = OTPLog.objects.filter(user=user).order_by('-created_at')[:10]
        today = timezone.now().date()
        stats = OTPLog.objects.filter(user=user).aggregate(
            total=Count('id'),
            delivered=Count('id', filter=models.Q(status='delivered')),
            avg_latency=Avg('latency_ms'),
        )
        ctx.update({
            'balance': balance,
            'recent_logs': recent_logs,
            'stats': stats,
            'active_keys': APIKey.objects.filter(user=user, status='active').count(),
        })
        return ctx


class AccountView(LoginRequiredMixin, View):
    login_url = 'login'
    template_name = 'fastotp/account.html'

    def get(self, request):
        sessions = LoginSession.objects.filter(user=request.user)[:10]
        return render(request, self.template_name, {'sessions': sessions})

    def post(self, request):
        user = request.user
        action = request.POST.get('action')

        if action == 'update_profile':
            user.first_name = request.POST.get('first_name', user.first_name)
            user.last_name = request.POST.get('last_name', user.last_name)
            user.company_name = request.POST.get('company_name', user.company_name)
            user.phone_number = request.POST.get('phone_number', user.phone_number)
            user.avatar_initials = ''  # Will be regenerated
            user.save()
            if 'HX-Request' in request.headers:
                return render(request, 'fastotp/partials/profile_success.html')
            messages.success(request, 'Profile updated.')

        elif action == 'change_password':
            current = request.POST.get('current_password', '')
            new_pw = request.POST.get('new_password', '')
            confirm = request.POST.get('confirm_password', '')
            if not user.check_password(current):
                if 'HX-Request' in request.headers:
                    return HttpResponse('<p class="text-red-400">Current password is incorrect.</p>')
                messages.error(request, 'Current password is incorrect.')
            elif new_pw != confirm:
                if 'HX-Request' in request.headers:
                    return HttpResponse('<p class="text-red-400">Passwords do not match.</p>')
                messages.error(request, 'New passwords do not match.')
            elif len(new_pw) < 8:
                if 'HX-Request' in request.headers:
                    return HttpResponse('<p class="text-red-400">Password too short (min 8 chars).</p>')
            else:
                user.set_password(new_pw)
                user.save()
                update_session_auth_hash(request, user)
                if 'HX-Request' in request.headers:
                    return render(request, 'fastotp/partials/password_success.html')
                messages.success(request, 'Password changed.')

        return redirect('account')


class DeveloperToolsView(LoginRequiredMixin, TemplateView):
    login_url = 'login'
    template_name = 'fastotp/developer.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['api_keys'] = APIKey.objects.filter(user=self.request.user)
        return ctx


class GenerateAPIKeyView(LoginRequiredMixin, View):
    login_url = 'login'

    def post(self, request):
        name = request.POST.get('name', 'New Key')
        env = request.POST.get('environment', 'test')
        key_obj = APIKey.objects.create(user=request.user, name=name, environment=env)
        if 'HX-Request' in request.headers:
            return render(request, 'fastotp/partials/api_key_row.html', {
                'key': key_obj,
                'show_full': True,
            })
        return redirect('developer')


class RevokeAPIKeyView(LoginRequiredMixin, View):
    login_url = 'login'

    def post(self, request, key_id):
        key_obj = get_object_or_404(APIKey, id=key_id, user=request.user)
        key_obj.status = 'revoked'
        key_obj.save()
        if 'HX-Request' in request.headers:
            return render(request, 'fastotp/partials/api_key_row.html', {'key': key_obj})
        return redirect('developer')


class OTPLogsView(LoginRequiredMixin, TemplateView):
    login_url = 'login'
    template_name = 'fastotp/otp_logs.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['logs'] = OTPLog.objects.filter(user=self.request.user)[:50]
        return ctx


class OTPLogsPollingView(LoginRequiredMixin, View):
    """HTMX polling endpoint for live OTP log updates."""
    login_url = 'login'

    def get(self, request):
        logs = OTPLog.objects.filter(user=request.user).order_by('-created_at')[:20]
        return render(request, 'fastotp/partials/otp_log_rows.html', {'logs': logs})


# ─────────────────────────────────────────────
#  Billing Views
# ─────────────────────────────────────────────

class BillingView(LoginRequiredMixin, TemplateView):
    login_url = 'login'
    template_name = 'fastotp/billing.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        balance, _ = CreditBalance.objects.get_or_create(user=user)
        packages = CreditPackage.objects.filter(is_active=True)
        transactions = Transaction.objects.filter(user=user)[:20]
        ctx.update({
            'balance': balance,
            'packages': packages,
            'transactions': transactions,
        })
        return ctx


class CreditBalancePollingView(LoginRequiredMixin, View):
    """HTMX polling for live balance updates."""

    def get(self, request):
        balance, _ = CreditBalance.objects.get_or_create(user=request.user)
        return render(request, 'fastotp/partials/credit_balance.html', {'balance': balance})


class InitiatePaymentView(LoginRequiredMixin, View):
    """Open the payment modal and generate a payment link."""
    login_url = 'login'

    def post(self, request):
        package_id = request.POST.get('package_id')
        gateway = request.POST.get('gateway', 'paystack')
        package = get_object_or_404(CreditPackage, id=package_id, is_active=True)
        user = request.user

        # Create a pending transaction
        txn = Transaction.objects.create(
            user=user,
            transaction_type='topup',
            amount_usd=package.price_usd,
            credits=package.credits,
            status='pending',
            gateway=gateway,
            package=package,
            description=f'{package.name} — {package.credits} credits',
        )

        payment_url = '#'
        if gateway == 'paystack':
            gw = PaystackGateway()
            result = gw.initialize_transaction(
                email=user.email,
                amount_kobo=int(float(package.price_usd) * 100 * 1600),  # approx NGN
                metadata={'user_id': str(user.id), 'package_id': str(package.id), 'txn_id': str(txn.id)},
                callback_url=request.build_absolute_uri('/billing/verify/paystack/'),
            )
            payment_url = result.get('authorization_url', '#')
            txn.gateway_ref = result.get('reference', '')
        else:
            gw = FlutterwaveGateway()
            result = gw.initialize_payment(
                tx_ref=str(txn.id),
                amount=float(package.price_usd),
                currency='USD',
                customer={'email': user.email, 'name': user.get_full_name()},
                redirect_url=request.build_absolute_uri('/billing/verify/flutterwave/'),
            )
            payment_url = result.get('link', '#')

        txn.save()

        if 'HX-Request' in request.headers:
            return render(request, 'fastotp/partials/payment_modal.html', {
                'package': package,
                'txn': txn,
                'payment_url': payment_url,
                'gateway': gateway,
            })
        return redirect(payment_url)


class PaymentCallbackView(View):
    """Handle payment gateway callbacks."""

    def get(self, request, gateway):
        if gateway == 'paystack':
            ref = request.GET.get('reference', '')
            gw = PaystackGateway()
            result = gw.verify_transaction(ref)
            if result.get('status') == 'success':
                try:
                    txn = Transaction.objects.get(gateway_ref=ref)
                    credit_user_account(txn.user, float(txn.credits), txn)
                    messages.success(request, f'✅ {int(txn.credits)} credits added to your account!')
                except Transaction.DoesNotExist:
                    messages.error(request, 'Transaction not found.')
        elif gateway == 'flutterwave':
            txn_id = request.GET.get('transaction_id', '')
            status = request.GET.get('status', '')
            if status == 'successful':
                try:
                    txn = Transaction.objects.get(gateway_ref=txn_id)
                    credit_user_account(txn.user, float(txn.credits), txn)
                    messages.success(request, f'✅ {int(txn.credits)} credits added!')
                except Transaction.DoesNotExist:
                    pass

        return redirect('billing')


# ─────────────────────────────────────────────
#  Seed Demo Data View (Dev only)
# ─────────────────────────────────────────────

class SeedDemoView(View):
    """Seed dummy OTP logs and packages for UI demonstration."""

    def get(self, request):
        from django.conf import settings
        if not settings.DEBUG:
            return HttpResponse('Not available in production.', status=403)

        # Seed packages
        packages = [
            {'name': 'Starter', 'tier': 'starter', 'credits': 500, 'price_usd': 5.00, 'price_per_otp': 0.010, 'features': ['500 OTPs', 'WhatsApp + SMS', 'Basic analytics', '99.9% uptime SLA']},
            {'name': 'Pro', 'tier': 'pro', 'credits': 5000, 'price_usd': 40.00, 'price_per_otp': 0.008, 'is_popular': True, 'features': ['5,000 OTPs', 'All channels', 'Advanced analytics', 'Priority support', '99.99% uptime SLA']},
            {'name': 'Enterprise', 'tier': 'enterprise', 'credits': 50000, 'price_usd': 350.00, 'price_per_otp': 0.007, 'features': ['50,000 OTPs', 'All channels', 'Dedicated infrastructure', '24/7 support', 'Custom sender ID', 'SLA guarantee']},
            {'name': 'Scale', 'tier': 'custom', 'credits': 200000, 'price_usd': 1200.00, 'price_per_otp': 0.006, 'features': ['200,000 OTPs', 'Custom contracts', 'Account manager', 'White-label option']},
        ]
        for p in packages:
            CreditPackage.objects.get_or_create(name=p['name'], defaults=p)

        if request.user.is_authenticated:
            user = request.user
            channels = ['whatsapp', 'sms', 'email']
            statuses = ['delivered', 'delivered', 'delivered', 'failed', 'pending', 'verified']
            countries = ['Nigeria', 'Kenya', 'Ghana', 'South Africa', 'Rwanda']
            for i in range(30):
                OTPLog.objects.create(
                    user=user,
                    identifier=f'+2348{random.randint(10000000, 99999999)}',
                    channel=random.choice(channels),
                    country_name=random.choice(countries),
                    status=random.choice(statuses),
                    latency_ms=random.randint(150, 1200),
                    cost_credits=random.uniform(0.004, 0.008),
                    sent_at=timezone.now() - timedelta(minutes=random.randint(0, 1440)),
                )

        return HttpResponse('Demo data seeded! <a href="/">Go home</a>')


# Helpers
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


# Import models.Q for aggregation
from django.db import models
