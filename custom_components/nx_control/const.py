"""Constants for NX Control."""
from datetime import timedelta

DOMAIN = "nx_control"
DEFAULT_PORT = 8460
CONF_TOKEN = "token"
CONF_CONSOLE_ID = "console_id"
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
