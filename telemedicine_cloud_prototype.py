"""
Design-validation prototype for the Telemedicine Cloud Architecture assignment.
This is NOT a production medical system and uses no real patient data.
It demonstrates API routing, workload isolation, scaling decisions and audit logging.
"""
from dataclasses import dataclass, field
from collections import Counter
import time

@dataclass
class VM:
    name: str
    workload: str
    capacity: int
    active: int = 0

@dataclass
class Gateway:
    routes: dict
    audit: list = field(default_factory=list)

    def request(self, service, user_role, payload):
        if service not in self.routes:
            raise ValueError("Unknown service")
        if not user_role:
            raise PermissionError("Authentication required")
        target = self.routes[service]
        self.audit.append({
            "service": service, "role": user_role, "target": target, "payload_keys": list(payload)
        })
        return {"status": "accepted", "service": service, "target": target}

def allocate_workloads(vms, workloads):
    result = {}
    for workload in workloads:
        candidates = [v for v in vms if v.workload == workload]
        if not candidates:
            result[workload] = None
            continue
        target = min(candidates, key=lambda v: v.active / max(v.capacity, 1))
        if target.active < target.capacity:
            target.active += 1
            result[workload] = target.name
        else:
            result[workload] = "SCALE_REQUIRED"
    return result

def main():
    vms = [
        VM("VM-EHR-1", "EHR", 5),
        VM("VM-EHR-2", "EHR", 5),
        VM("VM-VIDEO-1", "Telemedicine", 3),
        VM("VM-PACS-1", "PACS", 4),
    ]
    gateway = Gateway({
        "ehr": "VM-EHR-1/2",
        "telemedicine": "VM-VIDEO-1",
        "pacs": "VM-PACS-1"
    })

    print("TEST 1: authenticated EHR request")
    print(gateway.request("ehr", "doctor", {"patient_id": "DEMO"}))

    print("TEST 2: unauthenticated request")
    try:
        gateway.request("ehr", "", {"patient_id": "DEMO"})
    except PermissionError as e:
        print("PASS:", e)

    print("TEST 3: workload allocation and capacity check")
    requests = ["EHR"] * 11 + ["Telemedicine"] * 4 + ["PACS"] * 4
    allocations = allocate_workloads(vms, requests)
    print(Counter(allocations.values()))

    print("TEST 4: audit log entries")
    print("PASS:", len(gateway.audit) >= 1)

if __name__ == "__main__":
    main()
