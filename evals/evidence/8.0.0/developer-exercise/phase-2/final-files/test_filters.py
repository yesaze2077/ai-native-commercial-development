import copy
import unittest

from filters import filter_records


class FilterRecordsTests(unittest.TestCase):
    def setUp(self):
        self.records = [
            {"id": "a", "status": "open"},
            {"id": "b", "status": "closed"},
            {"id": "c", "status": "open"},
            {"id": "d"},
            {"id": "e", "status": "Open"},
        ]

    def test_no_filter_returns_new_list_in_original_order(self):
        results = [filter_records(self.records)]
        results.extend(filter_records(self.records, status) for status in (None, ""))
        for result in results:
            with self.subTest(result=result):
                self.assertEqual(result, self.records)
                self.assertIsNot(result, self.records)
                self.assertEqual([record["id"] for record in result], ["a", "b", "c", "d", "e"])

    def test_filters_exact_status_in_original_order(self):
        for status, expected_ids in (("open", ["a", "c"]), ("closed", ["b"])):
            with self.subTest(status=status):
                result = filter_records(self.records, status)
                self.assertEqual([record["id"] for record in result], expected_ids)

    def test_missing_null_and_different_case_status_do_not_match(self):
        records = [{"id": "missing"}, {"id": "null", "status": None}, {"id": "case", "status": "Open"}]
        for status in ("open", "closed"):
            with self.subTest(status=status):
                self.assertEqual(filter_records(records, status), [])

    def test_empty_list_with_valid_status_returns_new_empty_list(self):
        records = []
        for status in (None, "", "open", "closed"):
            with self.subTest(status=status):
                result = filter_records(records, status)
                self.assertEqual(result, [])
                self.assertIsNot(result, records)

    def test_invalid_status_raises_even_for_empty_input(self):
        invalid_statuses = ("Open", "CLOSED", "unknown", " ", 0, 1, False, True, [], {}, ["open"], ("open",))
        for records in (self.records, []):
            for status in invalid_statuses:
                with self.subTest(status=status, empty=not records):
                    with self.assertRaises(ValueError):
                        filter_records(records, status)

    def test_input_list_and_records_are_unchanged(self):
        before = copy.deepcopy(self.records)
        original_records = tuple(self.records)
        for status in (None, "", "open", "closed", "Open", []):
            with self.subTest(status=status):
                try:
                    filter_records(self.records, status)
                except ValueError:
                    pass
                self.assertEqual(self.records, before)
                self.assertEqual(len(self.records), len(original_records))
                for record, original in zip(self.records, original_records):
                    self.assertIs(record, original)


if __name__ == "__main__":
    unittest.main()
