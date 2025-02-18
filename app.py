from pypresence import Presence
import time
import pygetwindow as gw
import pystray
from PIL import Image
import threading
import sys
import os
import traceback
import logging
import requests
import webbrowser
from packaging import version

# Configuration
CURRENT_VERSION = "1.0.0"
CLIENT_ID = "1341446553394610236"

logging.basicConfig(
    filename='rpgmaker_rpc.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_resource_path(relative_path):
    try:
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_path, relative_path)
    except Exception as e:
        logging.error(f"Error getting resource path: {e}")
        return relative_path

def get_project_name():
    try:
        rpg_windows = gw.getWindowsWithTitle("RPG Maker MZ")
        if (rpg_windows):
            window = rpg_windows[0]
            project_name = window.title.split(" - ")[0]
            return project_name
    except Exception as e:
        logging.error(f"Error getting project name: {e}")
    return "RPG Maker MZ Project"  # Default project name in English

def check_for_updates():
    try:
        response = requests.get("https://api.github.com/repos/Inkflow59/RPGMakerMZ-DiscordRPC/releases/latest")
        if response.status_code == 200:
            latest_version = response.json()["tag_name"].replace("v", "")
            if version.parse(latest_version) > version.parse(CURRENT_VERSION):
                return latest_version, response.json()["html_url"]
    except requests.exceptions.RequestException as e:
        logging.error(f"Network error checking for updates: {e}")
    except ValueError as e:
        logging.error(f"Error processing update response: {e}")
    except Exception as e:
        logging.error(f"Error checking for updates: {e}")
    return None, None

def open_update_url(url):
    webbrowser.open(url)

def create_icon():
    try:
        icon_path = get_resource_path('ressource/icon.ico')  # The icon is in the resource folder
        logging.info(f"Loading icon from: {icon_path}")
        if os.path.exists(icon_path):
            return Image.open(icon_path)
        
        logging.warning("Icon not found, using default")
        return Image.new('RGB', (64, 64), color='white')
    except Exception as e:
        logging.error(f"Error creating icon: {e}")
        return Image.new('RGB', (64, 64), color='white')

def stop_application(icon):
    try:
        icon.stop()
    except Exception as e:
        logging.error(f"Error stopping icon: {e}")
    os._exit(0)

def run_discord_rpc():
    while True:
        try:
            RPC = Presence(CLIENT_ID)
            RPC.connect()
            logging.info("Discord Rich Presence connected!")
            
            while True:
                try:
                    project_name = get_project_name()
                    RPC.update(
                        large_image="rpgmz_logo",
                        large_text="RPG Maker MZ",
                        details=project_name,
                        state="In development",  # Changed to English
                        start=time.time()
                    )
                    time.sleep(15)
                except Exception as e:
                    logging.error(f"Error updating presence: {e}")
                    time.sleep(15)
                    break
                    
        except Exception as e:
            logging.error(f"Error in Discord RPC: {e}")
            logging.info("Retrying in 30 seconds...")
            time.sleep(30)

def check_updates_periodically(icon):
    while True:
        try:
            latest_version, update_url = check_for_updates()
            menu_items = [pystray.MenuItem(f"Current version: {CURRENT_VERSION}", lambda: None)]
            
            if latest_version:
                menu_items.append(
                    pystray.MenuItem(
                        f"Update to v{latest_version}", 
                        lambda: open_update_url(update_url)
                    )
                )
            
            menu_items.append(pystray.MenuItem("Quit", stop_application))
            icon.menu = pystray.Menu(*menu_items)
            
            time.sleep(3600)  # Check every hour
        except Exception as e:
            logging.error(f"Error in update check thread: {e}")
            time.sleep(3600)

def main():
    try:
        icon = pystray.Icon(
            "rpgmz-rpc",
            icon=create_icon(),
            menu=pystray.Menu(
                pystray.MenuItem("Checking for updates...", lambda: None),
                pystray.MenuItem("Quit", stop_application)
            )
        )

        # Start Discord RPC thread
        discord_thread = threading.Thread(target=run_discord_rpc, daemon=True)
        discord_thread.start()

        # Start update check thread
        update_thread = threading.Thread(target=check_updates_periodically, args=(icon,), daemon=True)
        update_thread.start()
        
        logging.info("Starting system tray icon...")
        icon.run()
    except Exception as e:
        logging.critical(f"Critical error in main: {e}")
        logging.critical(traceback.format_exc())

if __name__ == "__main__":
    main()