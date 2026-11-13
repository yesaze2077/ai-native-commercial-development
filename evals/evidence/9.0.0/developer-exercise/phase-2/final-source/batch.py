def apply_batch(items, updater):
    """Apply each pure callback once, retaining successes after item failures."""
    succeeded = []
    failed = []
    for item in items:
        try:
            value = updater(item)
        except Exception as error:
            failed.append({"id": item, "error": str(error)})
        else:
            succeeded.append({"id": item, "value": value})
    return {"succeeded": succeeded, "failed": failed}
