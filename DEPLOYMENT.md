# Deployment Guide - Smart City Parking System

This guide provides step-by-step instructions for deploying the Smart City Parking System to production.

## 🚀 Deployment Options

### Option 1: Render (Recommended)

Render provides free hosting with automatic deployments from GitHub.

#### Steps:

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/yourusername/smartcity-parking.git
   git push -u origin main
   ```

2. **Create Render Account**
   - Go to https://render.com
   - Sign up with GitHub

3. **Create New Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Configure:
     - **Name**: smartcity-parking
     - **Environment**: Python
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `gunicorn app:app`
     - **Instance Type**: Free

4. **Add Environment Variables**
   Go to "Environment" tab and add:
   ```
   SECRET_KEY=your-secret-key
   JWT_SECRET_KEY=your-jwt-secret-key
   MONGO_URI=your-mongodb-atlas-uri
   RAZORPAY_KEY_ID=your-razorpay-key
   RAZORPAY_KEY_SECRET=your-razorpay-secret
   NOWPAYMENTS_API_KEY=your-nowpayments-key
   GOOGLE_MAPS_API_KEY=your-google-maps-key
   ```

5. **Deploy**
   - Click "Create Web Service"
   - Render will automatically deploy your app
   - Your app will be live at: `https://smartcity-parking.onrender.com`

---

### Option 2: Railway

Railway offers simple deployments with excellent developer experience.

#### Steps:

1. **Create Railway Account**
   - Go to https://railway.app
   - Sign up with GitHub

2. **Create New Project**
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository
   - Railway will auto-detect Python

3. **Add Environment Variables**
   - Go to "Variables" tab
   - Add all environment variables (same as Render)

4. **Deploy**
   - Railway automatically deploys
   - Get your URL from the "Settings" tab

---

### Option 3: PythonAnywhere

Good for Python projects with free tier.

#### Steps:

1. **Create Account**
   - Go to https://www.pythonanywhere.com
   - Sign up for free account

2. **Upload Code**
   - Go to "Files" tab
   - Upload your project or clone from GitHub

3. **Setup Virtual Environment**
   ```bash
   mkvirtualenv --python=/usr/bin/python3.10 myenv
   pip install -r requirements.txt
   ```

4. **Configure WSGI**
   - Go to "Web" tab → "Add a new web app"
   - Choose "Manual configuration"
   - Edit WSGI configuration file:
   ```python
   import sys
   path = '/home/yourusername/smartcity-parking'
   if path not in sys.path:
       sys.path.append(path)
   
   from app import create_app
   application = create_app()
   ```

5. **Set Environment Variables**
   - Add to WSGI file or use .env file

---

### Option 4: Heroku

Traditional PaaS with good documentation.

#### Steps:

1. **Install Heroku CLI**
   ```bash
   # macOS
   brew tap heroku/brew && brew install heroku
   
   # Windows
   # Download from https://devcenter.heroku.com/articles/heroku-cli
   ```

2. **Login and Create App**
   ```bash
   heroku login
   heroku create smartcity-parking
   ```

3. **Add MongoDB Add-on**
   ```bash
   heroku addons:create mongolab:sandbox
   ```

4. **Set Environment Variables**
   ```bash
   heroku config:set SECRET_KEY=your-secret-key
   heroku config:set JWT_SECRET_KEY=your-jwt-secret-key
   heroku config:set RAZORPAY_KEY_ID=your-razorpay-key
   # ... add all variables
   ```

5. **Deploy**
   ```bash
   git push heroku main
   ```

---

## 🗄️ Database Setup (MongoDB Atlas)

All deployment options require a cloud MongoDB instance.

### Steps:

1. **Create MongoDB Atlas Account**
   - Go to https://www.mongodb.com/cloud/atlas
   - Sign up for free

2. **Create Cluster**
   - Choose free M0 tier
   - Select region closest to your users
   - Create cluster (takes 1-3 minutes)

3. **Create Database User**
   - Go to "Database Access"
   - Add new user with password
   - Grant "Read and write to any database" role

4. **Whitelist IP**
   - Go to "Network Access"
   - Add IP: `0.0.0.0/0` (allow from anywhere)
   - Or add specific IPs for security

5. **Get Connection String**
   - Click "Connect" on your cluster
   - Choose "Connect your application"
   - Copy connection string
   - Replace `<password>` with your database password
   - Example: `mongodb+srv://user:pass@cluster0.xxxxx.mongodb.net/?appName=Cluster0`

---

## 💳 Payment Gateway Setup

### Razorpay (INR Payments)

1. **Create Account**
   - Go to https://razorpay.com
   - Sign up and complete KYC

2. **Get API Keys**
   - Go to Settings → API Keys
   - Generate Test/Live keys
   - Copy Key ID and Key Secret

3. **Configure Webhooks** (Optional)
   - Go to Settings → Webhooks
   - Add webhook URL: `https://your-domain.com/api/payment/webhook`

### NOWPayments (Crypto Payments)

1. **Create Account**
   - Go to https://nowpayments.io
   - Sign up

2. **Get API Key**
   - Go to Settings → API Keys
   - Generate API key

3. **Configure IPN** (Optional)
   - Set IPN URL for payment notifications

---

## 🔒 Security Checklist

Before going to production:

- [ ] Change all default keys in `.env`
- [ ] Use strong SECRET_KEY (generate with: `python -c "import secrets; print(secrets.token_hex(32))"`)
- [ ] Enable HTTPS (automatically provided by Render/Railway)
- [ ] Whitelist specific IPs for MongoDB (not 0.0.0.0/0)
- [ ] Set up proper CORS origins (not `*`)
- [ ] Enable rate limiting
- [ ] Set up monitoring and logging
- [ ] Back up database regularly
- [ ] Review all API keys and rotate if needed

---

## 📊 Monitoring

### Application Monitoring

1. **Sentry (Error Tracking)**
   ```bash
   pip install sentry-sdk[flask]
   ```
   
   Add to `app.py`:
   ```python
   import sentry_sdk
   from sentry_sdk.integrations.flask import FlaskIntegration
   
   sentry_sdk.init(
       dsn="your-sentry-dsn",
       integrations=[FlaskIntegration()]
   )
   ```

2. **Uptime Monitoring**
   - Use UptimeRobot (https://uptimerobot.com)
   - Monitor endpoint: `https://your-domain.com/health`

### Database Monitoring

- Use MongoDB Atlas built-in monitoring
- Set up alerts for high CPU/memory usage
- Monitor connection pool usage

---

## 🔄 Continuous Deployment

### GitHub Actions

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Render

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to Render
        run: |
          curl -X POST ${{ secrets.RENDER_DEPLOY_HOOK_URL }}
```

Add `RENDER_DEPLOY_HOOK_URL` to GitHub Secrets.

---

## 🧪 Testing Production

After deployment, test these endpoints:

1. **Health Check**
   ```bash
   curl https://your-domain.com/health
   ```

2. **Register User**
   ```bash
   curl -X POST https://your-domain.com/api/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email":"test@test.com","password":"pass123","name":"Test","phone":"1234567890","role":"driver"}'
   ```

3. **Login**
   ```bash
   curl -X POST https://your-domain.com/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"test@test.com","password":"pass123"}'
   ```

---

## 🆘 Troubleshooting

### Common Issues

1. **502 Bad Gateway**
   - Check if app is running: View logs in Render/Railway
   - Verify PORT environment variable
   - Check Procfile syntax

2. **Database Connection Failed**
   - Verify MONGO_URI is correct
   - Check if IP is whitelisted in MongoDB Atlas
   - Ensure database user has correct permissions

3. **Import Errors**
   - Ensure all dependencies in requirements.txt
   - Check Python version compatibility
   - Clear build cache and redeploy

4. **Static Files Not Loading**
   - Check UPLOAD_FOLDER path
   - Verify file permissions
   - Consider using cloud storage (AWS S3, Cloudinary)

### Viewing Logs

**Render:**
- Go to your service → Logs tab

**Railway:**
- Click on your service → View Logs

**Heroku:**
```bash
heroku logs --tail
```

---

## 📈 Scaling

When your app grows:

1. **Upgrade Database**
   - Move to paid MongoDB Atlas tier
   - Enable replica sets
   - Add indexes for frequently queried fields

2. **Upgrade Hosting**
   - Render: Upgrade to paid instance
   - Railway: Add more resources
   - Consider load balancer for multiple instances

3. **Add Caching**
   - Use Redis for session storage
   - Cache frequently accessed data
   - Implement CDN for static files

4. **Background Jobs**
   - Use Celery for async tasks
   - Process payments in background
   - Send emails asynchronously

---

## 🎉 You're Live!

Your Smart City Parking System is now deployed and ready to use!

**Next Steps:**
1. Share your API URL with frontend developers
2. Set up monitoring and alerts
3. Create documentation for your team
4. Start onboarding users!

For support, contact: akash.bluee@gmail.com
