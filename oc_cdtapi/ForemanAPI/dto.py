from dataclasses import dataclass
from typing import List, Optional


def _to_int(value):
    """
    :param value: number (or numeric string) from the JSON response
    :return: int, or None when the value is missing or not a number
    """
    try:
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return None


@dataclass
class PartitionUsage:
    """
    Usage of one guest partition, as reported by VMware Tools (fog-vsphere 'partitions').
    Sizes are in bytes.
    """
    path: str
    capacity: Optional[int]
    free: Optional[int]

    @property
    def used_percent(self) -> Optional[float]:
        """
        :return: float, used space in percent, or None when capacity or free space is unknown
        """
        if self.capacity is None or self.capacity <= 0 or self.free is None:
            return None
        return 100 * (self.capacity - self.free) / self.capacity

    @classmethod
    def from_json(cls, data):
        """
        :param data: dict, e.g. {"path": "/", "free": 2147483648, "capacity": 10737418240}
        :return: PartitionUsage, or None when the entry has no path
        """
        if not isinstance(data, dict):
            return None
        path = data.get("path")
        if not isinstance(path, str) or not path:
            return None
        return cls(
            path=path,
            capacity=_to_int(data.get("capacity")),
            free=_to_int(data.get("free")),
        )

    def to_json(self):
        return {
            "path": self.path,
            "free": self.free,
            "capacity": self.capacity,
        }


def _partitions_from_json(entries):
    """
    :param entries: list of partition entries from the response, or None
    :return: list of PartitionUsage, or None when there is no usable entry
    """
    if not isinstance(entries, list):
        return None
    partitions = [PartitionUsage.from_json(entry) for entry in entries]
    partitions = [partition for partition in partitions if partition is not None]
    return partitions or None


@dataclass
class HostComputeAttributes:
    cpus: Optional[int]
    memory_mb: Optional[int]
    disk_size: Optional[int]
    power_state: Optional[str]
    # None when there is no partition data, e.g. a powered-off VM or a VM without VMware Tools
    partitions: Optional[List[PartitionUsage]] = None

    @classmethod
    def from_json(cls, data):
        # a host without a compute resource may have an empty (null) response
        data = data or {}
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
            partitions=_partitions_from_json(data.get("partitions")),
        )

    def to_json(self):
        partitions = None
        if self.partitions is not None:
            partitions = [partition.to_json() for partition in self.partitions]
        return {
            "cpus": self.cpus,
            "memory_mb": self.memory_mb,
            "disk_size": self.disk_size,
            "power_state": self.power_state,
            "partitions": partitions,
        }
