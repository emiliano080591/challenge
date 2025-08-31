import json, logging, sys


class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


logger = logging.getLogger("kopi")
logger.setLevel(logging.getLevelName("DEBUG"))
h = logging.StreamHandler(sys.stdout)
h.setFormatter(JsonFormatter())
logger.handlers = [h]
logger.propagate = False
