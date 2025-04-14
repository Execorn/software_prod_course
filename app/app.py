import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, request, jsonify, Response
import datetime


LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", "/app/logs/app.log")
LOG_LEVEL_STR = os.getenv("LOG_LEVEL", "INFO").upper()
APP_PORT = int(os.getenv("APP_PORT", 8080))
WELCOME_MESSAGE = os.getenv(
    "WELCOME_MESSAGE", "Welcome to the Fibonacci Calculator App"
)
MAX_LOG_BYTES = 10 * 1024 * 1024
LOG_BACKUP_COUNT = 5


log_level = getattr(logging, LOG_LEVEL_STR, logging.INFO)
log_dir = os.path.dirname(LOG_FILE_PATH)
if log_dir and not os.path.exists(log_dir):
    os.makedirs(log_dir, exist_ok=True)


log_formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
log_handler = RotatingFileHandler(
    LOG_FILE_PATH, maxBytes=MAX_LOG_BYTES, backupCount=LOG_BACKUP_COUNT
)
log_handler.setFormatter(log_formatter)


logger = logging.getLogger(__name__)
logger.setLevel(log_level)
logger.addHandler(log_handler)


app = Flask(__name__)


app.logger.addHandler(log_handler)
app.logger.setLevel(log_level)


def fibonacci(n):
    if n < 0:
        raise ValueError("Input must be a non-negative integer")
    elif n == 0:
        return 0
    elif n == 1:
        return 1
    else:
        a, b = 0, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        return b


@app.route("/")
def index():
    logger.info("Root endpoint '/' accessed")
    return WELCOME_MESSAGE


@app.route("/status")
def status():
    logger.debug("Status endpoint '/status' accessed")
    return jsonify(
        {"status": "ok", "timestamp": datetime.datetime.utcnow().isoformat()}
    )


@app.route("/log", methods=["POST"])
def log_message():
    try:
        data = request.get_json()
        if not data or "message" not in data:
            logger.warning("Received invalid log request: missing 'message' field")
            return (
                jsonify({"error": "Invalid JSON format, 'message' field required"}),
                400,
            )

        log_entry = data["message"]
        logger.info(f"Received log via POST: {log_entry}")
        return jsonify({"status": "logged"}), 200
    except Exception as e:
        logger.error(f"Error processing /log request: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@app.route("/logs")
def get_logs():
    logger.debug("Log retrieval endpoint '/logs' accessed")
    try:

        if not os.path.exists(LOG_FILE_PATH):
            with open(LOG_FILE_PATH, "a") as f:
                f.write("")

        with open(LOG_FILE_PATH, "r") as f:
            log_content = f.read()

        return Response(log_content, mimetype="text/plain")
    except FileNotFoundError:
        logger.warning(f"Log file not found at {LOG_FILE_PATH}")
        return Response("Log file not found.", status=404, mimetype="text/plain")
    except Exception as e:
        logger.error(f"Error reading log file: {e}", exc_info=True)
        return Response(
            f"Error reading log file: {e}", status=500, mimetype="text/plain"
        )


@app.route("/fibonacci/<int:n>", methods=["GET"])
def get_fibonacci(n):
    logger.info(f"Fibonacci endpoint '/fibonacci/{n}' accessed")
    try:
        result = fibonacci(n)
        logger.debug(f"Calculated Fibonacci({n}) = {result}")
        return jsonify({"n": n, "fibonacci": result})
    except ValueError as ve:
        logger.warning(f"Invalid input for Fibonacci: {ve}")
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        logger.error(f"Error calculating Fibonacci({n}): {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    logger.info(
        f"Starting Fibonacci App on port {APP_PORT} with log level {LOG_LEVEL_STR}"
    )

    app.run(host="0.0.0.0", port=APP_PORT)
