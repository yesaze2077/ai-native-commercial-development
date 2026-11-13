def filter_records(records, status=None):
    if status is None:
        return list(records)
    if not isinstance(status, str) or status not in ("", "open", "closed"):
        raise ValueError("status must be None, '', 'open', or 'closed'")
    if status == "":
        return list(records)
    return [record for record in records if record.get("status") == status]
