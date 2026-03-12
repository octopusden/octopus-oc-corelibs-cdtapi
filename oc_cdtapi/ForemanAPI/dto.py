from dataclasses import dataclass
from typing import Optional


@dataclass
class HostComputeAttributes:
    cpus: int
    memory_mb: Optional[int]
    disk_size: Optional[int]
    power_state: Optional[str]

    @classmethod
    def from_json(cls, data):
        disk_size = None
        volumes = data.get("volumes_attributes", {})
        volume = volumes.get("0") or volumes.get(0)
        if volume and "size_gb" in volume:
            disk_size = int(volume["size_gb"])
        return cls(
            memory_mb=data.get("memory_mb", None),
            cpus=data.get("cpus", None),
            disk_size=disk_size,
            power_state=data.get("power_state", None),
        )

    def to_json(self):
        return {
            "cpus": self.cpus,
            "memory_mb": self.memory_mb,
            "disk_size": self.disk_size,
            "power_state": self.power_state,
        }
