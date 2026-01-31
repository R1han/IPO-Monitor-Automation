import os
import sys
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
import finnhub
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

# Load environment variables
load_dotenv()

# Configuration
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")

# Minimum offer amount threshold in USD
MIN_OFFER_AMOUNT = 200_000_000  


def validate_config():
    """Validate that all required environment variables are set."""
    missing = []
    if not FINNHUB_API_KEY:
        missing.append("FINNHUB_API_KEY")
    if not SENDGRID_API_KEY:
        missing.append("SENDGRID_API_KEY")
    if not SENDER_EMAIL:
        missing.append("SENDER_EMAIL")
    if not RECIPIENT_EMAIL:
        missing.append("RECIPIENT_EMAIL")
    
    if missing:
        print(f"Error: Missing environment variables: {', '.join(missing)}")
        print("Please check your .env file.")
        sys.exit(1)


def get_today_date():
    """Get today's date in Dubai timezone (UTC+4)."""
    dubai_tz = timezone(timedelta(hours=4))
    today = datetime.now(dubai_tz).strftime("%Y-%m-%d")
    return today


def fetch_ipo_calendar(finnhub_client, from_date, to_date):
    """Fetch IPO calendar from Finnhub."""
    try:
        ipo_data = finnhub_client.ipo_calendar(_from=from_date, to=to_date)
        return ipo_data.get("ipoCalendar", [])
    except Exception as e:
        print(f"Error fetching IPO calendar: {e}")
        return []


def filter_qualifying_ipos(ipos, target_date):
    """
    Filter IPOs that:
    1. Have IPO date matching today (same day only)
    2. Have offer amount above $200 million
    """
    qualifying_ipos = []
    
    for ipo in ipos:
        ipo_date = ipo.get("date", "")
        
        # Check if IPO is for today only
        if ipo_date != target_date:
            continue
        
        # Calculate offer amount (price × numberOfShares)
        price = ipo.get("price", 0) or 0
        shares = ipo.get("numberOfShares", 0) or 0
        
        # Handle price ranges (e.g., "15-17" -> use midpoint)
        if isinstance(price, str) and "-" in price:
            try:
                low, high = price.split("-")
                price = (float(low) + float(high)) / 2
            except ValueError:
                price = 0
        
        try:
            price = float(price)
            shares = int(shares)
        except (ValueError, TypeError):
            price = 0
            shares = 0
        
        offer_amount = price * shares
        
        if offer_amount >= MIN_OFFER_AMOUNT:
            qualifying_ipos.append({
                "symbol": ipo.get("symbol", "N/A"),
                "name": ipo.get("name", "N/A"),
                "date": ipo_date,
                "price": price,
                "shares": shares,
                "offer_amount": offer_amount,
                "exchange": ipo.get("exchange", "N/A"),
            })
    
    return qualifying_ipos


def format_currency(amount):
    """Format amount as currency string."""
    if amount >= 1_000_000_000:
        return f"${amount / 1_000_000_000:.2f}B"
    elif amount >= 1_000_000:
        return f"${amount / 1_000_000:.2f}M"
    else:
        return f"${amount:,.2f}"


def create_email_content(qualifying_ipos, today):
    """Create HTML email content."""
    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .header {{ background-color: #1a73e8; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; }}
            table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            th {{ background-color: #1a73e8; color: white; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            .highlight {{ color: #1a73e8; font-weight: bold; }}
            .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🔔 IPO Alert - {today}</h1>
        </div>
        <div class="content">
            <p>The following IPOs are scheduled for <strong>today ({today})</strong> with offer amounts exceeding <span class="highlight">$200 Million</span>:</p>
            
            <table>
                <tr>
                    <th>Ticker</th>
                    <th>Company Name</th>
                    <th>Exchange</th>
                    <th>Price</th>
                    <th>Shares</th>
                    <th>Offer Amount</th>
                </tr>
    """
    
    for ipo in qualifying_ipos:
        html_content += f"""
                <tr>
                    <td><strong>{ipo['symbol']}</strong></td>
                    <td>{ipo['name']}</td>
                    <td>{ipo['exchange']}</td>
                    <td>${ipo['price']:.2f}</td>
                    <td>{ipo['shares']:,}</td>
                    <td class="highlight">{format_currency(ipo['offer_amount'])}</td>
                </tr>
        """
    
    html_content += """
            </table>
            
            <div class="footer">
                <p>This is an automated alert from the IPO Monitor script.</p>
                <p>Data source: Finnhub API</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_content


def create_no_ipo_email_content(today):
    """Create email content when no qualifying IPOs are found."""
    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .header {{ background-color: #6c757d; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; text-align: center; }}
            .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📊 IPO Update - {today}</h1>
        </div>
        <div class="content">
            <h2>No Qualifying IPOs Today</h2>
            <p>There are no U.S. stock market IPOs scheduled for today ({today}) with offer amounts exceeding $200 Million.</p>
        </div>
        <div class="footer">
            <p>This is an automated alert from the IPO Monitor script.</p>
            <p>Data source: Finnhub API</p>
        </div>
    </body>
    </html>
    """
    return html_content


def send_email(subject, html_content):
    """Send email via SendGrid."""
    try:
        message = Mail(
            from_email=Email(SENDER_EMAIL),
            to_emails=To(RECIPIENT_EMAIL),
            subject=subject,
            html_content=Content("text/html", html_content)
        )
        
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        
        if response.status_code in [200, 201, 202]:
            print(f"Email sent successfully! Status code: {response.status_code}")
            return True
        else:
            print(f"Email send failed with status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def main():
    """Main function to run the IPO monitor."""
    print("=" * 50)
    print("IPO Monitor Script")
    print("=" * 50)
    
    # Validate configuration
    validate_config()
    
    # Get today's date
    today = get_today_date()
    print(f"\nChecking IPOs for: {today}")
    
    # Initialize Finnhub client
    finnhub_client = finnhub.Client(api_key=FINNHUB_API_KEY)
    
    # Fetch IPO calendar (check a range to ensure we catch today's IPOs)
    ipos = fetch_ipo_calendar(finnhub_client, today, today)
    print(f"Found {len(ipos)} IPO(s) in calendar for today")
    
    # Filter qualifying IPOs
    qualifying_ipos = filter_qualifying_ipos(ipos, today)
    print(f"Qualifying IPOs (>$200M offer amount): {len(qualifying_ipos)}")
    
    # Prepare and send email
    if qualifying_ipos:
        # List ticker symbols
        tickers = [ipo['symbol'] for ipo in qualifying_ipos]
        print(f"\nQualifying tickers: {', '.join(tickers)}")
        
        subject = f"IPO Alert: {len(qualifying_ipos)} IPO(s) Today - {', '.join(tickers)}"
        html_content = create_email_content(qualifying_ipos, today)
    else:
        subject = f"IPO Update: No Qualifying IPOs - {today}"
        html_content = create_no_ipo_email_content(today)
    
    # Send the email
    print("\nSending email notification...")
    success = send_email(subject, html_content)
    
    if success:
        print("\nIPO Monitor completed successfully!")
    else:
        print("\nIPO Monitor completed with errors.")
        sys.exit(1)


if __name__ == "__main__":
    main()
