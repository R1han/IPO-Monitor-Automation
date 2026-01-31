# IPO Monitor

Automated script to monitor U.S. stock market IPOs and send email alerts for IPOs with offer amounts exceeding $200 million.

## Features

- Fetches IPO calendar from Finnhub API
- Filters for **same-day IPOs only** (not future dates)
- Identifies IPOs with offer amount (price × shares) > $200M
- Sends formatted HTML email via SendGrid
- Runs daily at 9:00 AM Dubai time (UTC+4)

## Setup

### 1. Install Dependencies

```bash
cd /Users/rihan/Personal_Repo/Quant/ipo_monitor
pip install -r requirements.txt
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your credentials:

| Variable | Description |
|----------|-------------|
| `FINNHUB_API_KEY` | Get free API key at [finnhub.io](https://finnhub.io/) |
| `SENDGRID_API_KEY` | Get API key at [sendgrid.com](https://sendgrid.com/) |
| `SENDER_EMAIL` | Must be verified in SendGrid |
| `RECIPIENT_EMAIL` | Email to receive alerts |

### 3. Test the Script

```bash
python3 ipo_monitor.py
```

### 4. Setup Cron Job

```bash
chmod +x setup_cron.sh
./setup_cron.sh
```

Or manually add to crontab:
```bash
crontab -e
```

Add this line (9 AM Dubai = 5 AM UTC):
```
0 5 * * * cd /Users/rihan/Personal_Repo/Quant/ipo_monitor && python3 ipo_monitor.py >> ipo_monitor.log 2>&1
```

## Getting API Keys

### Finnhub API Key (Free)
1. Go to [finnhub.io](https://finnhub.io/)
2. Sign up for a free account
3. Copy your API key from the dashboard

### SendGrid API Key (Free tier: 100 emails/day)
1. Go to [sendgrid.com](https://sendgrid.com/)
2. Sign up for a free account
3. Go to Settings → API Keys → Create API Key
4. **Important**: Verify your sender email address under Settings → Sender Authentication

## File Structure

```
ipo_monitor/
├── ipo_monitor.py      # Main script
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variables template
├── .env                # Your actual credentials (git-ignored)
├── setup_cron.sh       # Cron job setup script
├── ipo_monitor.log     # Log file (created on first run)
└── README.md           # This file
```

## Troubleshooting

### Email not sending
- Verify sender email in SendGrid dashboard
- Check SendGrid API key has "Mail Send" permission
- Check `ipo_monitor.log` for errors

### No IPOs found
- Finnhub's free tier has IPO data for major exchanges
- Some IPOs may not have price data until closer to the date

### Cron not running
- Check if cron daemon is running: `pgrep cron`
- Verify crontab: `crontab -l`
- Check system logs: `log show --predicate 'process == "cron"' --last 1h`

## License

MIT
