import logging
import re


class PrivateURLFilter(logging.Filter):
    """Do not place bearer access/calendar tokens in application log messages."""
    def filter(self, record):
        message = record.getMessage()
        record.msg = re.sub(r'/(access|calendar|verify-email)/[^\s?]+', r'/\1/[redacted]', message)
        record.args = ()
        return True
