# Copyright The OpenTelemetry Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from enum import Enum
from typing import Final

HW_BATTERY_CAPACITY: Final = "hw.battery.capacity"
"""
Design capacity in Watts-hours or Amper-hours.
"""

HW_BATTERY_CHEMISTRY: Final = "hw.battery.chemistry"
"""
Battery [chemistry](https://schemas.dmtf.org/wbem/cim-html/2.31.0/CIM_Battery.html), e.g. Lithium-Ion, Nickel-Cadmium, etc.
"""

HW_BATTERY_STATE: Final = "hw.battery.state"
"""
The current state of the battery.
"""

HW_BIOS_VERSION: Final = "hw.bios_version"
"""
BIOS version of the hardware component.
"""

HW_DRIVER_VERSION: Final = "hw.driver_version"
"""
Driver version for the hardware component.
"""

HW_ENCLOSURE_TYPE: Final = "hw.enclosure.type"
"""
Type of the enclosure (useful for modular systems).
"""

HW_FIRMWARE_VERSION: Final = "hw.firmware_version"
"""
Firmware version of the hardware component.
"""

HW_GPU_TASK: Final = "hw.gpu.task"
"""
Type of task the GPU is performing.
"""

HW_ID: Final = "hw.id"
"""
An identifier for the hardware component, unique within the monitored host.
"""

HW_LIMIT_TYPE: Final = "hw.limit_type"
"""
Type of limit for hardware components.
"""

HW_LOGICAL_DISK_RAID_LEVEL: Final = "hw.logical_disk.raid_level"
"""
RAID Level of the logical disk.
"""

HW_LOGICAL_DISK_STATE: Final = "hw.logical_disk.state"
"""
State of the logical disk space usage.
"""

HW_MEMORY_TYPE: Final = "hw.memory.type"
"""
Type of the memory module.
"""

HW_MODEL: Final = "hw.model"
"""
Descriptive model name of the hardware component.
"""

HW_NAME: Final = "hw.name"
"""
An easily-recognizable name for the hardware component.
"""

HW_NETWORK_LOGICAL_ADDRESSES: Final = "hw.network.logical_addresses"
"""
Logical addresses of the adapter (e.g. IP address, or WWPN).
"""

HW_NETWORK_PHYSICAL_ADDRESS: Final = "hw.network.physical_address"
"""
Physical address of the adapter (e.g. MAC address, or WWNN).
"""

HW_PARENT: Final = "hw.parent"
"""
Unique identifier of the parent component (typically the `hw.id` attribute of the enclosure, or disk controller).
"""

HW_PHYSICAL_DISK_SMART_ATTRIBUTE: Final = "hw.physical_disk.smart_attribute"
"""
[S.M.A.R.T.](https://wikipedia.org/wiki/S.M.A.R.T.) (Self-Monitoring, Analysis, and Reporting Technology) attribute of the physical disk.
"""

HW_PHYSICAL_DISK_STATE: Final = "hw.physical_disk.state"
"""
State of the physical disk endurance utilization.
"""

HW_PHYSICAL_DISK_TYPE: Final = "hw.physical_disk.type"
"""
Type of the physical disk.
"""

HW_SENSOR_LOCATION: Final = "hw.sensor_location"
"""
Location of the sensor.
"""

HW_SERIAL_NUMBER: Final = "hw.serial_number"
"""
Serial number of the hardware component.
"""

HW_STATE: Final = "hw.state"
"""
The current state of the component.
"""

HW_TAPE_DRIVE_OPERATION_TYPE: Final = "hw.tape_drive.operation_type"
"""
Type of tape drive operation.
"""

HW_TYPE: Final = "hw.type"
"""
Type of the component.
Note: Describes the category of the hardware component for which `hw.state` is being reported. For example, `hw.type=temperature` along with `hw.state=degraded` would indicate that the temperature of the hardware component has been reported as `degraded`.
"""

HW_VENDOR: Final = "hw.vendor"
"""
Vendor name of the hardware component.
"""


class HwBatteryStateValues(Enum):
    CHARGING = "charging"
    """Charging."""
    DISCHARGING = "discharging"
    """Discharging."""


class HwGpuTaskValues(Enum):
    DECODER = "decoder"
    """Decoder."""
    ENCODER = "encoder"
    """Encoder."""
    GENERAL = "general"
    """General."""


class HwLimitTypeValues(Enum):
    CRITICAL = "critical"
    """Critical."""
    DEGRADED = "degraded"
    """Degraded."""
    HIGH_CRITICAL = "high.critical"
    """High Critical."""
    HIGH_DEGRADED = "high.degraded"
    """High Degraded."""
    LOW_CRITICAL = "low.critical"
    """Low Critical."""
    LOW_DEGRADED = "low.degraded"
    """Low Degraded."""
    MAX = "max"
    """Maximum."""
    THROTTLED = "throttled"
    """Throttled."""
    TURBO = "turbo"
    """Turbo."""


class HwLogicalDiskStateValues(Enum):
    USED = "used"
    """Used."""
    FREE = "free"
    """Free."""


class HwPhysicalDiskStateValues(Enum):
    REMAINING = "remaining"
    """Remaining."""


class HwStateValues(Enum):
    DEGRADED = "degraded"
    """Degraded."""
    FAILED = "failed"
    """Failed."""
    NEEDS_CLEANING = "needs_cleaning"
    """Needs Cleaning."""
    OK = "ok"
    """OK."""
    PREDICTED_FAILURE = "predicted_failure"
    """Predicted Failure."""


class HwTapeDriveOperationTypeValues(Enum):
    MOUNT = "mount"
    """Mount."""
    UNMOUNT = "unmount"
    """Unmount."""
    CLEAN = "clean"
    """Clean."""


class HwTypeValues(Enum):
    BATTERY = "battery"
    """Battery."""
    CPU = "cpu"
    """CPU."""
    DISK_CONTROLLER = "disk_controller"
    """Disk controller."""
    ENCLOSURE = "enclosure"
    """Enclosure."""
    FAN = "fan"
    """Fan."""
    GPU = "gpu"
    """GPU."""
    LOGICAL_DISK = "logical_disk"
    """Logical disk."""
    MEMORY = "memory"
    """Memory."""
    NETWORK = "network"
    """Network."""
    PHYSICAL_DISK = "physical_disk"
    """Physical disk."""
    POWER_SUPPLY = "power_supply"
    """Power supply."""
    TAPE_DRIVE = "tape_drive"
    """Tape drive."""
    TEMPERATURE = "temperature"
    """Temperature."""
    VOLTAGE = "voltage"
    """Voltage."""
