# Liquity Trove Management Script

Sends pushover ( https://pushover.net/ ) notification when:
- Trove's collateral ratio is outside of defined limits
- Trove is at risk of redemption according to defined limits
- Trove's debt or collateral are modified

### Installation:
1. Clone repository and install requirements: See requirements.txt
1. Rename .env_template to .env and input required information
1. Test command:
    ```
    python trove_management.py --force-notification
    ```
1. Command to create cron job to check trove health every hour (run from project directory):
    ```
    crontab -l | { cat; echo "30 * * * * $(which python) $(pwd)/trove_management.py"; } | crontab -
    ```
1. Command to create cron job to notify trove's status every day at at noon (run from project directory):
    ```
    crontab -l | { cat; echo "0 12 * * * $(which python) $(pwd)/trove_management.py --force-notification"; } | crontab -
    ```
