# FastOTP — Africa's Fastest OTP Delivery Platform

A production-grade Django application for OTP delivery across Africa.

## Tech Stack
- Django 4.2+ (DTL templates, CBVs)
- Tailwind CSS via CDN (Emerald/Lime/Slate palette)
- HTMX for seamless partial updates & live polling
- Alpine.js for micro-interactions
- SQLite (dev) / PostgreSQL (production)

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set environment variables (copy .env.example)
cp .env.example .env

# 3. Run migrations
python manage.py migrate

# 4. Create superuser (optional)
python manage.py createsuperuser

# 5. Start dev server
python manage.py runserver
```

## Environment Variables (.env)

```
DJANGO_SECRET_KEY=your-very-secret-key-here
DEBUG=True
PAYSTACK_SECRET_KEY=sk_test_xxx
FLUTTERWAVE_SECRET_KEY=FLWSECK_TEST-xxx
FASTOTP_API_KEY=fotk_live_xxx
```

## Seed Demo Data
Visit `http://localhost:8000/dev/seed/` (only in DEBUG mode) to populate:
- 4 credit packages (Starter, Pro, Enterprise, Scale)
- 30 demo OTP log entries (if logged in)

## Project Structure

```
fastotp/
├── config/
│   ├── settings.py          # Django settings
│   └── urls.py              # Root URL conf
├── fastotp/
│   ├── models.py            # All models
│   ├── views.py             # All CBVs
│   ├── urls.py              # App URL conf
│   └── services.py          # FastOTP SDK + Payment stubs
├── templates/fastotp/
│   ├── base.html            # Global base
│   ├── dashboard_base.html  # Dashboard layout with sidebar
│   ├── home.html            # Landing page
│   ├── coverage.html        # Coverage & Rates
│   ├── signup_step1.html    # Registration form
│   ├── signup_step2.html    # WhatsApp OTP verification
│   ├── login.html           # Login
│   ├── dashboard.html       # Main dashboard
│   ├── developer.html       # API key management
│   ├── billing.html         # Credits & payments
│   ├── otp_logs.html        # Live OTP log
│   ├── account.html         # Profile settings
│   ├── privacy.html         # Privacy policy
│   ├── terms.html           # Terms of service
│   └── partials/
│       ├── otp_input.html        # HTMX: OTP digit input + countdown
│       ├── otp_success.html      # HTMX: verification success
│       ├── otp_error.html        # HTMX: verification error
│       ├── otp_log_rows.html     # HTMX: live log rows (polling)
│       ├── api_key_row.html      # HTMX: single API key row
│       ├── credit_balance.html   # HTMX: balance badge (polling)
│       └── payment_modal.html    # HTMX: payment dialog
└── requirements.txt
```

## Key Features

### HTMX Interactions
- **Signup OTP**: Button swaps to 6-digit input + lime countdown timer
- **OTP Logs**: Auto-refresh every 10s via polling
- **API Keys**: Generate/revoke without page reload
- **Credit Balance**: Polls every 30s in sidebar and billing page
- **Payment Modal**: Opens inline via HTMX swap

### Design System
- **Primary**: `#059669` Emerald Green
- **Accent**: `#bef264` Lime (speed/success indicators)
- **Background**: `#f8fafc` Soft Slate
- **Cards**: Glassmorphism with `backdrop-filter: blur(20px)`
- **Rounded corners**: 24px (`rounded-3xl`)
- **Buttons**: Push effect on click (`transform: scale(0.97)`)
- **Pending status**: Shimmer animation

### Payment Integration (Stubs)
Services.py contains fully documented stubs for:
- **Paystack**: `PaystackGateway.initialize_transaction()` + `verify_transaction()`
- **Flutterwave**: `FlutterwaveGateway.initialize_payment()` + `verify_payment()`

Replace stub methods with real SDK calls after installing:
```bash
pip install paystackapi flutterwave3
```
