import unittest

from batch import apply_batch


class ApplyBatchTests(unittest.TestCase):
    def test_all_succeed(self):
        result = apply_batch(["second", "first"], str.upper)
        self.assertEqual(result, {
            "succeeded": [
                {"id": "second", "value": "SECOND"},
                {"id": "first", "value": "FIRST"},
            ],
            "failed": [],
        })

    def test_mixed_failure_retains_successes_and_continues(self):
        def updater(item):
            if item == "bad":
                raise ValueError("invalid recommendation")
            return "updated:" + item

        result = apply_batch(["before", "bad", "after"], updater)
        self.assertEqual(result, {
            "succeeded": [
                {"id": "before", "value": "updated:before"},
                {"id": "after", "value": "updated:after"},
            ],
            "failed": [{"id": "bad", "error": "invalid recommendation"}],
        })

    def test_all_fail_in_encounter_order(self):
        def updater(item):
            raise RuntimeError("failed:" + item)

        self.assertEqual(apply_batch(["second", "first"], updater), {
            "succeeded": [],
            "failed": [
                {"id": "second", "error": "failed:second"},
                {"id": "first", "error": "failed:first"},
            ],
        })

    def test_empty_list(self):
        def updater(item):
            self.fail("empty input must not invoke the callback")

        self.assertEqual(apply_batch([], updater), {"succeeded": [], "failed": []})

    def test_callback_called_once_per_item_in_input_order(self):
        calls = []

        def updater(item):
            calls.append(item)
            if item == "bad":
                raise Exception("callback failure")
            return item

        apply_batch(["first", "bad", "last"], updater)
        self.assertEqual(calls, ["first", "bad", "last"])

    def test_input_is_not_modified(self):
        items = ["second", "first"]
        original = items.copy()
        apply_batch(items, str.upper)
        self.assertEqual(items, original)


if __name__ == "__main__":
    unittest.main()
