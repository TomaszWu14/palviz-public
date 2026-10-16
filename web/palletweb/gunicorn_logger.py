"""US-006 / S-07: logger gunicorna maskujący tokeny linków publicznych w logu dostępowym.

Włączany w docker-entrypoint.sh flagą `--logger-class palletweb.gunicorn_logger.MaskingLogger`.
"""
from gunicorn.glogging import Logger

from core.logmask import mask_tokens

# Atomy formatu logu dostępowego, które mogą nieść ścieżkę: linia żądania, ścieżka,
# referer (strona z linkiem może przejść dalej z tokenem w Referer).
_PATH_ATOMS = ("r", "U", "f")


class MaskingLogger(Logger):
    def atoms(self, resp, req, environ, request_time):
        atoms = super().atoms(resp, req, environ, request_time)
        for key in _PATH_ATOMS:
            if key in atoms:
                atoms[key] = mask_tokens(atoms[key])
        return atoms
