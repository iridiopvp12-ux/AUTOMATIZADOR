import os
import datetime

# Global variable to store the current session log file path
current_session_file = None

def start_session_log(username):
    """
    Starts a new log session for the given username.
    Creates a file in 'logs/' directory with format session_{username}_{timestamp}.txt
    """
    global current_session_file
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    # Sanitize username to prevent path traversal or invalid chars
    safe_username = "".join(c for c in username if c.isalnum() or c in ('-', '_'))
    filename = f"session_{safe_username}_{timestamp}.txt"
    log_dir = "logs"

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    current_session_file = os.path.join(log_dir, filename)

    with open(current_session_file, "w", encoding="utf-8") as f:
        f.write(f"Session started for user: {username} at {datetime.datetime.now()}\n")
        f.write("-" * 50 + "\n")

def log_action(message):
    """
    Logs an action to the current session file.
    """
    global current_session_file
    if current_session_file:
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        with open(current_session_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
    else:
        print(f"Warning: No active session log. Message: {message}")
