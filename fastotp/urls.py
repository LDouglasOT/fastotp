from django.urls import path
from . import views

urlpatterns = [
    # ── Marketing
    path('', views.HomeView.as_view(), name='home'),
    path('coverage/', views.CoverageView.as_view(), name='coverage'),
    path('privacy/', views.PrivacyView.as_view(), name='privacy'),
    path('terms/', views.TermsView.as_view(), name='terms'),

    # ── Auth
    path('signup/', views.SignupStep1View.as_view(), name='signup'),
    path('signup/verify/', views.SignupStep2View.as_view(), name='signup_step2'),
    path('signup/send-otp/', views.SendSignupOTPView.as_view(), name='send_signup_otp'),
    path('signup/verify-otp/', views.VerifySignupOTPView.as_view(), name='verify_signup_otp'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),

    # ── Dashboard
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('dashboard/account/', views.AccountView.as_view(), name='account'),
    path('dashboard/developer/', views.DeveloperToolsView.as_view(), name='developer'),
    path('dashboard/developer/keys/generate/', views.GenerateAPIKeyView.as_view(), name='generate_key'),
    path('dashboard/developer/keys/<uuid:key_id>/revoke/', views.RevokeAPIKeyView.as_view(), name='revoke_key'),
    path('dashboard/logs/', views.OTPLogsView.as_view(), name='otp_logs'),
    path('dashboard/logs/poll/', views.OTPLogsPollingView.as_view(), name='otp_logs_poll'),

    # ── Billing
    path('billing/', views.BillingView.as_view(), name='billing'),
    path('billing/balance/poll/', views.CreditBalancePollingView.as_view(), name='credit_balance_poll'),
    path('billing/pay/', views.InitiatePaymentView.as_view(), name='initiate_payment'),
    path('billing/verify/<str:gateway>/', views.PaymentCallbackView.as_view(), name='payment_callback'),

    # ── Dev utils
    path('dev/seed/', views.SeedDemoView.as_view(), name='seed_demo'),
]
