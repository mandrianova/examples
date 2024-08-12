import signal
import sys
import traceback
from datetime import datetime
from functools import wraps
from pathlib import Path
from string import Template

from . import JSONResponse, SignalHTTPError
from .aws_services.sns_manager import SNSEmailManager
from .logger import logger
from .main import get_log_link
from .response_handlers import Alert, AlertTypes
from .settings import (
    AWS_LAMBDA_FUNCTION_NAME,
    AWS_LAMBDA_LOG_GROUP_NAME,
    AWS_LAMBDA_LOG_STREAM_NAME,
    EXCEPTION_NOTIFY_ENDPOINTS,
    EXCEPTION_NOTIFY_TOPIC,
    STAGE,
)

STAGE = STAGE or "Unknown"

EXCEPTION_SUBJECT = Template("[${stage}] Exception Signals Integration | ${function_name}: ${error_type}")
EXCEPTION_TEMPLATE = Template(Path(__file__).parent.joinpath("exception_template.txt").read_text())


# Log uncaught exceptions
def log_uncaught_exceptions(ex_cls, ex, traceback_val):
    error_messages = traceback.format_exception(ex_cls, ex, traceback_val)
    logger.exception(ex)
    error = f"[{ex}]\n\n{''.join(error_messages)}"
    send_notification("Uncaught", error)
    sys.__excepthook__(ex_cls, ex, traceback_val)


sys.excepthook = log_uncaught_exceptions


def timeout_handler(signum, frame):
    raise TimeoutError("Lambda function is about to timeout!")


def lambda_middleware(lambda_handler):
    @wraps(lambda_handler)
    def wrap(event, context, *args, **kwargs):
        # Calculate the remaining time before timeout.
        # Subtracting a small buffer time (e.g., 1s) to ensure we catch the timeout before AWS does.
        buffer_time = 1  # seconds
        time_remaining = context.get_remaining_time_in_millis() / 1000 - buffer_time

        # Set the signal to trigger a TimeoutError before Lambda times out
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(int(time_remaining))

        try:
            logger.info(event)

            # Handle OPTIONS request.
            if event.get("httpMethod") == "OPTIONS":
                response = JSONResponse()
                return response.get_response()

            result = lambda_handler(event, context, *args, **kwargs)
            signal.alarm(0)  # Cancel the alarm if function completes in time
            return result

        except TimeoutError:
            logger.error("Lambda function timed out!")
            send_notification("Middleware", "Lambda function timed out!")
            if "httpMethod" in event:
                e = SignalHTTPError(504, "Lambda function Timeout")
                response = JSONResponse()
                response.errors = [e]
                response.alerts = [
                    Alert(
                        type=AlertTypes.danger,
                        text="Server Timeout Error\nTry again later or contact support",
                    ),
                ]
                return response.get_response()
            else:
                raise

        except Exception as error:  # noqa: BLE001
            error_message = f"[{error}]\n\n{traceback.format_exc()}"
            send_notification("Middleware", error_message)
            logger.exception(error_message)
            if "httpMethod" in event:
                e = SignalHTTPError(500, "Server error")
                response = JSONResponse()
                response.errors = [e]
                response.alerts = [
                    Alert(
                        type=AlertTypes.danger,
                        text="Server Side Error\nTry again later or contact support",
                    ),
                ]
                return response.get_response()
            else:
                raise error

    return wrap


def send_notification(error_type: str, error):
    subject = EXCEPTION_SUBJECT.substitute(
        stage=STAGE,
        error_type=error_type,
        function_name=AWS_LAMBDA_FUNCTION_NAME,
    )
    text = EXCEPTION_TEMPLATE.substitute(
        stage=STAGE,
        error_type=error_type,
        error=str(error),
        function_name=AWS_LAMBDA_FUNCTION_NAME,
        link=get_log_link(),
        log_group=AWS_LAMBDA_LOG_GROUP_NAME,
        log_stream=AWS_LAMBDA_LOG_STREAM_NAME,
        log_date=datetime.now().strftime("%Y%m%d %H:%M:%S"),
    )
    sns = SNSEmailManager(EXCEPTION_NOTIFY_TOPIC, EXCEPTION_NOTIFY_ENDPOINTS)
    sns.send_message(subject, text)
