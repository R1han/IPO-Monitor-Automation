SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_PATH=$(which python3)
LOG_FILE="$SCRIPT_DIR/ipo_monitor.log"

# Create the cron job entry
# 9:00 AM Dubai (UTC+4) = 5:00 AM UTC
CRON_JOB="0 5 * * * cd $SCRIPT_DIR && $PYTHON_PATH $SCRIPT_DIR/ipo_monitor.py >> $LOG_FILE 2>&1"

echo "=================================================="
echo "IPO Monitor - Cron Setup"
echo "=================================================="
echo ""
echo "Script directory: $SCRIPT_DIR"
echo "Python path: $PYTHON_PATH"
echo "Log file: $LOG_FILE"
echo ""
echo "Cron job to be added:"
echo "$CRON_JOB"
echo ""

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "ipo_monitor.py"; then
    echo " A cron job for ipo_monitor.py already exists."
    echo "Current crontab:"
    crontab -l | grep "ipo_monitor.py"
    echo ""
    read -p "Do you want to replace it? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Remove existing entry
        crontab -l 2>/dev/null | grep -v "ipo_monitor.py" | crontab -
    else
        echo "Keeping existing cron job. Exiting."
        exit 0
    fi
fi

# Add the cron job
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo ""
echo "Cron job added successfully!"
echo ""
echo "Verify with: crontab -l"
echo ""
echo "The script will run:"
echo "  - Every day at 9:00 AM Dubai time (5:00 AM UTC)"
echo "  - Logs will be saved to: $LOG_FILE"
echo ""
echo "=================================================="
echo "IMPORTANT: Before running, make sure to:"
echo "1. Copy .env.example to .env and fill in your API keys"
echo "2. Install dependencies: pip install -r requirements.txt"
echo "3. Test the script manually: python3 ipo_monitor.py"
echo "=================================================="
