from validators.abstracts.validator import Validator
from typing import Dict, Optional, List, Tuple
import json
from datetime import datetime


class InvoiceValidator(Validator):
    def __init__(self, invoice_data: Dict, ground_truth_po_numbers: Optional[List[str]] = None):
        super().__init__(invoice_data, ground_truth_po_numbers)
        self.price_accuracy_threshold = 95.0  # Case requirement: >95%
        self.po_accuracy_threshold = 90.0  # Case requirement: >90%

    def check_line_item_consistency(self) -> List[Dict]:
        """
        This function calculates the total price by multiplying the quantity of the relevant product with the unit price.
        The function compares the total values in the invoice with its own calculations and converts the result into a
        dictionary by reporting it in detail.
        :return: Analyzed line items consistency report list
        """
        inconsistencies = []
        for i, item in enumerate(self.line_items):
            quantity = item.get("quantity", 0)
            unit_price = item.get("unit_price", 0)
            total_price = item.get("total_price", 0)

            expected_total = round(quantity * unit_price, 2)
            actual_total = round(total_price, 2)

            if expected_total != actual_total:
                deviation_percent = abs(expected_total - actual_total) / max(expected_total, 0.01) * 100
                inconsistencies.append({
                    "index": i,
                    "item_name": item.get("item_name", "Unknown"),
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "expected_total": expected_total,
                    "actual_total": actual_total,
                    "deviation_amount": round(abs(expected_total - actual_total), 2),
                    "deviation_percent": round(deviation_percent, 2),
                    "severity": "high" if deviation_percent > 5 else "low"
                })
        return inconsistencies

    def check_total_consistency(self) -> Dict:
        """
        This function adds up the total value of all line items, then compares it with the value in the file.
        :return: Total consistency report dictionary
        """
        results = {
            "subtotal_correct": True,
            "vat_correct": True,
            "total_correct": True,
            "issues": [],
        }

        # Subtotal control
        expected_subtotal = round(sum(item.get("total_price", 0) for item in self.line_items), 2)
        actual_subtotal = round(self.total_details.get("subtotal", 0.0), 2)

        if expected_subtotal != actual_subtotal:
            results["subtotal_correct"] = False
            deviation = abs(expected_subtotal - actual_subtotal)
            results["issues"].append({
                "type": "subtotal_mismatch",
                "expected": expected_subtotal,
                "actual": actual_subtotal,
                "deviation": round(deviation, 2)
            })

        # Dynamic VAT rate detection
        vat_key = next((k for k in self.total_details if "vat" in k.lower()), None)
        if vat_key:
            # Extracting VAT value with regex
            import re
            vat_rate_match = re.search(r'\((\d+(?:\.\d+)?)\%?\)', vat_key)
            vat_rate = float(vat_rate_match.group(1)) / 100 if vat_rate_match else 0.20

            expected_vat = round(expected_subtotal * vat_rate, 2)
            actual_vat = round(self.total_details.get(vat_key, 0.0), 2)

            # Comparing VAT values
            if expected_vat != actual_vat:
                results["vat_correct"] = False
                deviation = abs(expected_vat - actual_vat)
                results["issues"].append({
                    "type": "vat_mismatch",
                    "expected": expected_vat,
                    "actual": actual_vat,
                    "deviation": round(deviation, 2),
                    "rate_used": vat_rate
                })

        return results

    def calculate_price_accuracy(self) -> Dict:
        """
        This function calculates price accuracy by summing up all the line totals.
        :return: Price accuracy report dictionary
        """
        line_inconsistencies = self.check_line_item_consistency()
        total_consistency = self.check_total_consistency()

        total_items = len(self.line_items)
        correct_line_items = total_items - len(line_inconsistencies)

        line_accuracy = (correct_line_items / max(total_items, 1)) * 100
        total_checks = 3  # subtotal, VAT and total
        correct_totals = sum([
            total_consistency["subtotal_correct"],
            total_consistency["vat_correct"],
            total_consistency["total_correct"]
        ])
        total_accuracy = (correct_totals / total_checks) * 100

        # Calculating overall accuracy for reporting
        overall_accuracy = (line_accuracy + total_accuracy) / 2

        return {
            "line_item_accuracy": round(line_accuracy, 2),
            "total_calculation_accuracy": round(total_accuracy, 2),
            "overall_price_accuracy": round(overall_accuracy, 2),
            "meets_requirement": overall_accuracy >= self.price_accuracy_threshold,
            "threshold": self.price_accuracy_threshold,
        }

    def report_missing_po_numbers(self) -> Dict:
        """
        This function reports missing PO numbers from the line items.
        :return: Missing PO numbers report dictionary
        """
        po_in_invoice = self.invoice_data.get("invoice_details", {}).get("po_number")
        po_in_lines = [item.get("po_number") for item in self.line_items if item.get("po_number")]

        missing_count = 0
        total_locations = 1 + len(self.line_items)  # invoice + line items

        if not po_in_invoice or po_in_invoice in (None, "", "null"):
            missing_count += 1

        missing_count += sum(1 for item in self.line_items
                             if not item.get("po_number") or item.get("po_number") in (None, "", "null"))

        return {
            "po_number_status": "missing" if missing_count == total_locations else "partial" if missing_count > 0 else "complete",
            "missing_locations": missing_count,
            "total_locations": total_locations,
            "coverage_percent": round(((total_locations - missing_count) / total_locations) * 100, 2),
            "found_pos": {
                "invoice_level": po_in_invoice if po_in_invoice and po_in_invoice not in (None, "", "null") else None,
                "line_level": po_in_lines
            }
        }

    def calculate_po_detection_accuracy(self) -> Dict:
        """
        This function calculates PO detection accuracy by using ground truth PO numbers given.
        :return: PO detection report dictionary
        """
        detected_pos = []

        # Invoice level PO
        invoice_po = self.invoice_data.get("invoice_details", {}).get("po_number")
        if invoice_po and invoice_po not in (None, "", "null"):
            detected_pos.append(invoice_po)

        # Line item level POs
        line_pos = [
            item["po_number"]
            for item in self.line_items
            if item.get("po_number") not in (None, "", "null")
        ]
        detected_pos.extend(line_pos)

        # Getting unique POs
        detected_pos = list(set(detected_pos))

        if not self.ground_truth_po_numbers or len(self.ground_truth_po_numbers) == 0:
            # If there is no ground truth, that means there is 100% accuracy for POs
            if len(detected_pos) == 0:
                return {
                    "po_accuracy": 100.0,
                    "meets_requirement": True,
                    "threshold": self.po_accuracy_threshold,
                    "scenario": "no_po_expected_none_detected",
                    "note": "No PO numbers expected (ground truth empty) and none detected - Perfect match",
                    "ground_truth_count": 0,
                    "detected_count": 0,
                    "false_detections": []
                }
            else:
                return {
                    "po_accuracy": 0.0,
                    "meets_requirement": False,
                    "threshold": self.po_accuracy_threshold,
                    "scenario": "no_po_expected_but_detected",
                    "note": f"No PO numbers expected but {len(detected_pos)} were detected - False positives",
                    "ground_truth_count": 0,
                    "detected_count": len(detected_pos),
                    "false_detections": detected_pos
                }

        correct_detections = [po for po in detected_pos if po in self.ground_truth_po_numbers]

        missed_pos = [po for po in self.ground_truth_po_numbers if po not in detected_pos]

        # Incorrectly detected POs
        false_detections = [po for po in detected_pos if po not in self.ground_truth_po_numbers]

        accuracy = (len(correct_detections) / len(self.ground_truth_po_numbers)) * 100

        return {
            "po_accuracy": round(accuracy, 2),
            "meets_requirement": accuracy >= self.po_accuracy_threshold,
            "threshold": self.po_accuracy_threshold,
            "scenario": "normal_po_detection",
            "ground_truth_count": len(self.ground_truth_po_numbers),
            "detected_count": len(detected_pos),
            "correct_detections": len(correct_detections),
            "missed_pos": missed_pos,
            "false_detections": false_detections,
            "details": {
                "ground_truth": self.ground_truth_po_numbers,
                "detected": detected_pos,
                "correct": correct_detections
            }
        }

    def _calculate_health_score(self, price_accuracy: Dict, po_detection: Dict, anomaly_count: int) -> int:
        """
        This function calculates overall health score of the file at the range of 0-100.
        :return: Overall health score for given case
        """
        score = 100

        if not price_accuracy["meets_requirement"]:
            score -= (100 - price_accuracy["overall_price_accuracy"]) * 0.4

        # No penalty if PO is not expected (ground truth empty) and never detected
        if not po_detection["meets_requirement"]:
            if po_detection.get("scenario") != "no_po_expected_none_detected":
                score -= (100 - po_detection["po_accuracy"]) * 0.4

        # Anomaly penalty
        score -= min(anomaly_count * 5, 20)  # Maximum 20 point penalty

        return max(0, int(score))

    def generate_report(self, filename: str) -> Dict:
        """
        This function combines other validator and report generator functions to get the complete report of the file.
        :param filename: Filename to generate report
        :return: General report of the file
        """
        report_timestamp = datetime.now().isoformat()

        # Basic control results
        line_item_issues = self.check_line_item_consistency()
        total_consistency = self.check_total_consistency()
        price_accuracy = self.calculate_price_accuracy()
        po_detection = self.calculate_po_detection_accuracy()
        po_presence = self.report_missing_po_numbers()

        # Report structure
        validation_report = {
            "metadata": {
                "filename": filename,
                "validation_timestamp": report_timestamp,
            },
            "summary": {
                "price_accuracy_status": "PASS" if price_accuracy["meets_requirement"] else "FAIL",
                "po_detection_status": "PASS" if po_detection["meets_requirement"] else "FAIL",
            },
            "price_validation": {
                "accuracy_metrics": price_accuracy,
                "line_item_issues": line_item_issues,
                "total_calculation_issues": total_consistency
            },
            "po_validation": {
                "detection_metrics": po_detection,
                "presence_analysis": po_presence
            }
        }

        # Adding report to original invoice data
        enriched_data = self.invoice_data.copy()
        enriched_data["validation_report"] = validation_report

        return enriched_data
