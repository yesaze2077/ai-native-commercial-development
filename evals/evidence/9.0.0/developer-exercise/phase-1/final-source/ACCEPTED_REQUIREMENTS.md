# Accepted synthetic requirements baseline
Internal operator reviews a list of recommendations, selects items, applies them, and sees per-item completion/recovery information. This local fixture uses synthetic string IDs and a supplied pure callback, without real system writes. The core outcome and batch action are approved.

# Experience / technical decision still open
When some callbacks fail, all-or-nothing rollback versus retaining successes has not been selected. Documented as OPEN. The caller needs a stable result/error contract after that decision.
