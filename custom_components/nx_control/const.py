"""Constants for NX Control."""
from datetime import timedelta

DOMAIN = "nx_control"
DEFAULT_PORT = 8460
CONF_TOKEN = "token"
CONF_CONSOLE_ID = "console_id"
CONF_NOTIFY_DEVICES = "notify_devices"
CONF_NOTIFY_RESULTS = "notify_results"
CONF_SIDEBAR = "sidebar"                  # NX Control page in the sidebar (default on)
PANEL_URL = "nx-control"                  # /nx-control
CONF_NOTIFY_TEST = "notify_test"          # send a test notification (not stored)
CONF_NOTIFY_OPEN = "notify_open"          # page opened when tapping a notification
SCAN_INTERVAL = timedelta(seconds=10)

EVENT_TIME_REQUEST = "nx_control_time_request"
EVENT_SESSION_STARTED = "nx_control_session_started"
EVENT_SESSION_ENDED = "nx_control_session_ended"

PLAYING_STATES = {"playing", "warning", "grace"}

SERVICE_GRANT_TIME = "grant_time"
SERVICE_APPROVE_REQUEST = "approve_request"
SERVICE_DENY_REQUEST = "deny_request"
SERVICE_BLOCK_PROFILE = "block_profile"
SERVICE_UNBLOCK_PROFILE = "unblock_profile"

CARD_URL = "/nx_control/nx-control-card.js"
IMAGE_URL = "/api/nx_control/image"

ATTR_PROFILE_ID = "profile_id"
ATTR_REQUEST_ID = "request_id"
ATTR_MINUTES = "minutes"
ATTR_MESSAGE = "message"
