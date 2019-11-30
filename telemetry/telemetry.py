# -*- coding: utf-8 -*-
import datetime
import functools
import os
import sys
from typing import Optional

from loguru import logger as log
from statsd import StatsClient

# Logging
LOG_LEVEL = os.environ.get("LOG_LEVEL", "DEBUG")

# Perfomance monitoring
STATSD_ON = os.environ.get("STATSD_ON", "false").lower() in ["true", "ok", "yes"]
STATSD_HOST = os.environ.get("STATSD_HOST", "localhost")
STATSD_PORT = os.environ.get("STATSD_PORT", "8125")
STATSD_PREFIX = os.environ.get("STATSD_PREFIX", "dev.app")
STATSD_MAXUDPSIZE = os.environ.get("STATSD_MAXUDPSIZE", "512")

config = {
    "handlers": [
        {
            "sink": sys.stdout,
            "format": (
                "{time:YYYY-MM-DD HH:mm:ss}"
                " | <level>{level: <4}</level>"
                " | <c>{name}</c>:<c>{function}</c>:<c>{line}</c> - <level>{message}</level>"
            ),
            "level": LOG_LEVEL,
        }
    ]
}

log.configure(**config)


class TelemetryService:
    def __init__(self, logger, prefix: str, statsd_client: Optional[StatsClient], method: Optional[str], reraise: bool):
        self.log = logger
        self.stat = statsd_client
        self._prefix = prefix
        self._method = method
        self._reraise = reraise

    def _method_name(self):
        return self._method if self._method else 'context_manager'

    def __enter__(self):
        method = self._method_name()

        self.method_call(method)

        self._start_time = datetime.datetime.utcnow()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        method = self._method_name()

        if exc_type is None and exc_value is None and exc_traceback is None:
            if self._start_time:
                self.method_success(method, timedelta=datetime.datetime.utcnow() - self._start_time)
            else:
                self.method_success(method)
        else:
            self.method_error(method, exc_value)

        self._start_time = None
        return None if self._reraise else True

    def method_call(self, method: str, **kwargs) -> None:
        msg = f"{self._prefix}.{method}.call"

        if self.stat is not None:
            self.stat.incr(f"{msg}.total", 1)
        self.log.debug(f"{msg},{kwargs}")

    def method_success(self, method: str, **kwargs) -> None:
        msg = f"{self._prefix}.{method}.success"

        dtkey = "timedelta"

        if self.stat is not None:
            self.stat.incr(f"{msg}.total", 1)
            if dtkey in kwargs:
                self.stat.timing(f"{msg}.total", kwargs[dtkey])

        if dtkey in kwargs:
            kwargs[dtkey] = str(kwargs[dtkey])
        self.log.debug(f"{msg},{kwargs}")

    def method_error(self, method: str, err: Exception, **kwargs) -> None:
        msg = f"{self._prefix}.{method}.error"

        if self.stat is not None:
            self.stat.incr(f"{msg}.total", 1)
        self.log.exception(f"{msg},{kwargs}", err)

    def catch(self, function=None, reraise: bool = True):
        if function is None:
            return functools.partial(self.catch, reraise=reraise)

        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            start_time = datetime.datetime.utcnow()
            self.method_call(function.__name__)
            try:
                result = function(*args, **kwargs)

                end_time = datetime.datetime.utcnow()
                self.method_success(function.__name__, timedelta=end_time - start_time)
                return result
            except Exception as err:
                self.method_error(function.__name__, err)
                if reraise:
                    raise

        return wrapper


def telemetry(name: str, logger=log, method: Optional[str] = None, reraise: bool = True) -> TelemetryService:
    statsd_client: StatsClient = (
        StatsClient(host=STATSD_HOST, port=STATSD_PORT, prefix=STATSD_PREFIX, maxudpsize=STATSD_MAXUDPSIZE, ipv6=False)
        if STATSD_ON
        else None
    )

    return TelemetryService(logger=logger, prefix=name, statsd_client=statsd_client, method=method, reraise=reraise)
