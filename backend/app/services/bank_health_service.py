import datetime
from typing import Dict, Any

class BankHealthService:
    def __init__(self):
        # Simulated live telemetry for top Indian banks
        self.bank_telemetry: Dict[str, Dict[str, Any]] = {
            "HDFC": {
                "name": "HDFC Bank",
                "success_rate": 96.4,
                "status": "HEALTHY",
                "npci_window_active": False,
                "preferred_window": "Immediate"
            },
            "SBI": {
                "name": "State Bank of India",
                "success_rate": 68.2, # Currently simulated degraded (NPCI nightly batch)
                "status": "DEGRADED",
                "npci_window_active": True,
                "preferred_window": "Tomorrow 06:30 AM"
            },
            "ICICI": {
                "name": "ICICI Bank",
                "success_rate": 94.8,
                "status": "HEALTHY",
                "npci_window_active": False,
                "preferred_window": "Immediate"
            },
            "AXIS": {
                "name": "Axis Bank",
                "success_rate": 91.5,
                "status": "HEALTHY",
                "npci_window_active": False,
                "preferred_window": "Immediate"
            }
        }

    def get_bank_health(self, bank_code: str = "HDFC") -> Dict[str, Any]:
        code = bank_code.upper()
        return self.bank_telemetry.get(code, {
            "name": f"{code} Bank",
            "success_rate": 92.0,
            "status": "HEALTHY",
            "npci_window_active": False,
            "preferred_window": "Immediate"
        })

    def get_all_banks(self) -> Dict[str, Dict[str, Any]]:
        return self.bank_telemetry

bank_health_service = BankHealthService()
