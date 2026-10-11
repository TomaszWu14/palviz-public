# Widoki transportu — importowane wprost w ui.urls (bez star-re-eksportu do
# ui.views: taki re-eksport robił cykl importu przez ui.views.core).
from .shipments import *  # noqa: F401,F403
from .driver import *  # noqa: F401,F403
