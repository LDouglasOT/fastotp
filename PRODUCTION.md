# FastOTP Deployment Guide

## Vercel Deployment

This guide covers deploying FastOTP to Vercel.

### Prerequisites

1. Vercel account
2. GitHub/GitLab/Bitbucket repository
3. Python 3.11+ project

### Deployment Steps

1. **Push code to Git**
   ```bash
   git add .
   git commit -m "Prepare for Vercel deployment"
   git push origin main
   ```

2. **Import to Vercel**
   - Go to [vercel.com](https://vercel.com)
   - Click "Add New..." → "Project"
   - Import your Git repository
   - Configure the following:
     - Framework Preset: Other
     - Build Command: (leave empty)
     - Output Directory: (leave empty)

3. **Environment Variables**
   In Vercel dashboard, add these environment variables:
   ```
   DJANGO_SECRET_KEY=your-secure-random-key-at-least-50-characters
   DEBUG=False
   VERCEL=1
   ```

   Optional (for production):
   ```
   PAYSTACK_SECRET_KEY=sk_live_...
   FLUTTERWAVE_SECRET_KEY=FLWSECK_TEST-...
   FASTOTP_API_KEY=fotk_live_...
   ```

4. **Deploy**
   - Click "Deploy"

### Database Note

Vercel's filesystem is ephemeral. For production:
- Use **Vercel Postgres** or **Neon** for the database
- Update `DATABASES` in settings.py to use the cloud database

Example for Vercel Postgres:
```python
import dj_database_url
DATABASES = {
    'default': dj_database_url.parse(os.environ.get('DATABASE_URL'))
}
```

### Static Files

Static files are handled by WhiteNoise and served through Vercel's CDN. The configuration is in:
- `vercel.json` - Vercel routes
- `config/settings.py` - WhiteNoise middleware

### Troubleshooting

1. **500 Error on first load**: Check that `DJANGO_SECRET_KEY` is set
2. **Static files not loading**: Ensure `whitenoise` is in requirements.txt
3. **Database errors**: Verify DATABASE_URL is set for production
