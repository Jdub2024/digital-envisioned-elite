# Digital Envisioned — Elite Automation Suite

**200-Tool Premium SaaS Platform · Built with Python & Streamlit**
*By Joshua Newton · Birmingham, AL · [digitalenvisioned.net](https://digitalenvisioned.net)*

---

## 🚀 Quick Start (Streamlit Cloud)

### 1. Push to GitHub

```bash
git init
git add .
git commit -m "Digital Envisioned Elite Automation Suite v1.0"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

### 2. Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click **"New app"**
3. Select your GitHub repo, branch `main`, and file `main.py`
4. Under **Advanced settings → Secrets**, add:
   ```toml
   RESEND_API_KEY = "re_XXXXXXXXXXXXXXXXXXXXXXXX"
   ```
5. Click **Deploy**

> **Note:** Streamlit Cloud reads secrets from `.streamlit/secrets.toml` or the Secrets UI. The app reads `RESEND_API_KEY` from `os.environ`. Streamlit Cloud automatically injects secrets as environment variables.

---

## 📁 Project Structure

```
├── main.py                  # Full application (6,200+ lines, 200 tools)
├── requirements.txt         # Python dependencies
├── README.md                # This file
├── attached_assets/
│   ├── de-logo.jpg                    # Hero logo (required)
│   ├── marketing-boost-brand.jpg      # Social media marketing flyer
│   ├── beautiful-ads-trust.jpg        # Beautiful Ads Build Trust (clean)
│   ├── beautiful-ads-beforeafter.jpg  # Before/After comparison
│   ├── freedom-blueprint.png          # 10-Minute Freedom Blueprint
│   ├── ads-not-converting.jpg         # Ads Not Converting sales image
│   ├── de-portfolio-intro.png         # Portfolio intro with client work
│   └── ads-hit-hard.jpg              # HIT HARD marketing ad
└── .streamlit/
    └── secrets.toml         # (Optional) Local secrets file
```

---

## ⚙️ Environment Variables

| Variable | Required | Description |
|---|---|---|
| `RESEND_API_KEY` | Yes | API key from [resend.com](https://resend.com) for welcome emails |

### Setting Secrets for Streamlit Cloud

Create `.streamlit/secrets.toml` in your project root (do NOT commit this to GitHub):

```toml
RESEND_API_KEY = "re_your_api_key_here"
```

Or set it via the Streamlit Cloud dashboard under **App settings → Secrets**.

---

## 🏗️ Architecture

### Tier System
| Tier | Tools | Access |
|---|---|---|
| **Free** | 1–10 | Lead capture form (email required) |
| **Pro** | 1–50 | $47/month via Stripe |
| **Elite** | 1–200 | $197/month via Stripe |
| **Master** | 1–200 | Hard-coded admin bypass |

### Master Admin
- **Email:** `jnworkflow@gmail.com`
- **Access:** All 200 tools, no restrictions

### Tool Categories (16 Groups)
1. Content & Writing (1–25)
2. SEO & Marketing (26–50)
3. Image & Media (51–75)
4. Developer Tools (76–90)
5. Finance & Business Utility Engine (91–102)
6. SEO & Copywriting Vault (103–115)
7. Content & Text Utilities (116–125)
8. Data & List Management (126–135)
9. Web & Network Tools (136–145)
10. Advanced Design & Media (146–155)
11. Security & Network Utilities (156–160)
12. Writing, Code & Conversion (161–165)
13. Social Media & Marketing (166–175)
14. Local SEO & Marketing Frameworks (176–181)
15. Business & Operations (182–190)
16. Executive Strategy (191–200)

### Landing Page Features
- Full-width hero with branded logo
- 10 free tool visual showcase grid with HD images
- Lead capture form → auto-saves to `leads.csv`
- Welcome email automation via Resend (SDK + REST fallback)
- Stripe upgrade CTAs for Pro & Elite tiers
- Master Admin sign-in

---

## 🏃 Local Development

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO

# Install dependencies
pip install -r requirements.txt

# Set your Resend API key
export RESEND_API_KEY="re_your_api_key_here"

# Run the app
streamlit run main.py
```

---

## 📧 Email Integration (Resend)

The app sends a professional branded welcome email when a guest submits the lead capture form.

**Setup:**
1. Create a free account at [resend.com](https://resend.com)
2. Verify your domain (`digitalenvisioned.net`)
3. Generate an API key
4. Add it as `RESEND_API_KEY` in your environment/secrets

**Sender:** `Joshua Newton <newton@digitalenvisioned.net>`

---

## 💳 Stripe Integration

Upgrade links point to Stripe Checkout:
- **Pro ($47/mo):** Tools 1–50
- **Elite ($197/mo):** Tools 1–200

---

## 📄 License

Proprietary — Digital Envisioned LLC. All rights reserved.

---

*Built by Joshua Newton · Powered by Streamlit · 200 Tools Strong* 🔥
