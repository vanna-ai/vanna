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


from typing import (
    Callable,
    Final,
    Generator,
    Iterable,
    Optional,
    Sequence,
    Union,
)

from opentelemetry.metrics import (
    CallbackOptions,
    Counter,
    Meter,
    ObservableGauge,
    Observation,
    UpDownCounter,
)

# pylint: disable=invalid-name
CallbackT = Union[
    Callable[[CallbackOptions], Iterable[Observation]],
    Generator[Iterable[Observation], CallbackOptions, None],
]

HW_BATTERY_CHARGE: Final = "hw.battery.charge"
"""
Remaining fraction of battery charge
Instrument: gauge
Unit: 1
"""


def create_hw_battery_charge(
    meter: Meter, callbacks: Optional[Sequence[CallbackT]]
) -> ObservableGauge:
    """Remaining fraction of battery charge"""
    return meter.create_observable_gauge(
        name=HW_BATTERY_CHARGE,
        callbacks=callbacks,
        description="Remaining fraction of battery charge.",
        unit="1",
    )


HW_BATTERY_CHARGE_LIMIT: Final = "hw.battery.charge.limit"
"""
Lower limit of battery charge fraction to ensure proper operation
Instrument: gauge
Unit: 1
"""


def create_hw_battery_charge_limit(
    meter: Meter, callbacks: Optional[Sequence[CallbackT]]
) -> ObservableGauge:
    """Lower limit of battery charge fraction to ensure proper operation"""
    return meter.create_observable_gauge(
        name=HW_BATTERY_CHARGE_LIMIT,
        callbacks=callbacks,
        description="Lower limit of battery charge fraction to ensure proper operation.",
        unit="1",
    )


HW_BATTERY_TIME_LEFT: Final = "hw.battery.time_left"
"""
Time left before battery is completely charged or discharged
Instrument: gauge
Unit: s
"""


def create_hw_battery_time_left(
    meter: Meter, callbacks: Optional[Sequence[CallbackT]]
) -> ObservableGauge:
    """Time left before battery is completely charged or discharged"""
    return meter.create_observable_gauge(
        name=HW_BATTERY_TIME_LEFT,
        callbacks=callbacks,
        description="Time left before battery is completely charged or discharged.",
        unit="s",
    )


HW_CPU_SPEED: Final = "hw.cpu.speed"
"""
CPU current frequency
Instrument: gauge
Unit: Hz
"""


def create_hw_cpu_speed(
    meter: Meter, callbacks: Optional[Sequence[CallbackT]]
) -> ObservableGauge:
    """CPU current frequency"""
    return meter.create_observable_gauge(
        name=HW_CPU_SPEED,
        callbacks=callbacks,
        description="CPU current frequency.",
        unit="Hz",
    )


HW_CPU_SPEED_LIMIT: Final = "hw.cpu.speed.limit"
"""
CPU maximum frequency
Instrument: gauge
Unit: Hz
"""


def create_hw_cpu_speed_limit(
    meter: Meter, callbacks: Optional[Sequence[CallbackT]]
) -> ObservableGauge:
    """CPU maximum frequency"""
    return meter.create_observable_gauge(
        name=HW_CPU_SPEED_LIMIT,
        callbacks=callbacks,
        description="CPU maximum frequency.",
        unit="Hz",
    )


HW_ENERGY: Final = "hw.energy"
"""
Energy consumed by the component
Instrument: counter
Unit: J
"""


def create_hw_energy(meter: Meter) -> Counter:
    """Energy consumed by the component"""
    return meter.create_counter(
        name=HW_ENERGY,
        description="Energy consumed by the component.",
        unit="J",
    )


HW_ERRORS: Final = "hw.errors"
"""
Number of errors encountered by the component
Instrument: counter
Unit: {error}
"""


def create_hw_errors(meter: Meter) -> Counter:
    """Number of errors encountered by the component"""
    return meter.create_counter(
        name=HW_ERRORS,
        description="Number of errors encountered by the component.",
        unit="{error}",
    )


HW_FAN_SPEED: Final = "hw.fan.speed"
"""
Fan speed in revolutions per minute
Instrument: gauge
Unit: rpm
"""


def create_hw_fan_speed(
    meter: Meter, callbacks: Optional[Sequence[CallbackT]]
) -> ObservableGauge:
    """Fan speed in revolutions per minute"""
    return meter.create_observable_gauge(
        name=HW_FAN_SPEED,
        callbacks=callbacks,
        description="Fan speed in revolutions per minute.",
        unit="rpm",
    )


HW_FAN_SPEED_LIMIT: Final = "hw.fan.speed.limit"
"""
Speed limit in rpm
Instrument: gauge
Unit: rpm
"""


def create_hw_fan_speed_limit(
    meter: Meter, callbacks: Optional[Sequence[CallbackT]]
) -> ObservableGauge:
    """Speed limit in rpm"""
    return meter.create_observable_gauge(
        name=HW_FAN_SPEED_LIMIT,
        callbacks=callbacks,
        description="Speed limit in rpm.",
        unit="rpm",
    )


HW_FAN_SPEED_RATIO: Final = "hw.fan.speed_ratio"
"""
Fan speed expressed as a fraction of its maximum speed
Instrument: gauge
Unit: 1
"""


def create_hw_fan_speed_ratio(
    meter: Meter, callbacks: Optional[Sequence[CallbackT]]
) -> ObservableGauge:
    """Fan speed expressed as a fraction of its maximum speed"""
    return meter.create_observable_gauge(
        name=HW_FAN_SPEED_RATIO,
        callbacks=callbacks,
        description="Fan speed expressed as a fraction of its maximum speed.",
        unit="1",
    )


HW_GPU_IO: Final = "hw.gpu.io"
"""
Received and transmitted bytes by the GPU
Instrument: counter
Unit: By
"""


def create_hw_gpu_io(meter: Meter) -> Counter:
    """Received and transmitted bytes by the GPU"""
    return meter.create_counter(
        name=HW_GPU_IO,
        description="Received and transmitted bytes by the GPU.",
        unit="By",
    )


HW_GPU_MEMORY_LIMIT: Final = "hw.gpu.memory.limit"
"""
Size of the GPU memory
Instrument: updowncounter
Unit: By
"""


def create_hw_gpu_memory_limit(meter: Meter) -> UpDownCounter:
    """Size of the GPU memory"""
    return meter.create_up_down_counter(
        name=HW_GPU_MEMORY_LIMIT,
        description="Size of the GPU memory.",
        unit="By",
    )


HW_GPU_MEMORY_USAGE: Final = "hw.gpu.memory.usage"
"""
GPU memory used
Instrument: updowncounter
Unit: By
"""


def create_hw_gpu_memory_usage(meter: Meter) -> UpDownCounter:
    """GPU memory used"""
    return meter.create_up_down_counter(
        name=HW_GPU_MEMORY_USAGE,
        description="GPU memory used.",
        unit="By",
    )


HW_GPU_MEMORY_UTILIZATION: Final = "hw.gpu.memory.utilization"
"""
Fraction of GPU memory used
Instrument: gauge
Unit: 1
"""


def create_hw_gpu_memory_utilization(
    meter: Meter, callbacks: Optional[Sequence[CallbackT]]
) -> ObservableGauge:
    """Fraction of GPU memory used"""
    return meter.create_observable_gauge(
        name=HW_GPU_MEMORY_UTILIZATION,
        callbacks=callbacks,
        description="Fraction of GPU memory used.",
        unit="1",
    )


HW_GPU_UTILIZATION: Final = "hw.gpu.utilization"
"""
Fraction of time spent in a specific task
Instrument: gauge
Unit: 1
"""


def create_hw_gpu_utilization(
    meter: Meter, callbacks: Optional[Sequence[CallbackT]]
) -> ObservableGauge:
    """Fraction of time spent in a specific task"""
    return meter.create_observable_gauge(
        name=HW_GPU_UTILIZATION,
        callbacks=callbacks,
        description="Fraction of time spent in a specific task.",
        unit="1",
    )


HW_HOST_AMBIENT_TEMPERATURE: Final = "hw.host.ambient_temperature"
"""
Ambient (external) temperature of the physical host
Instrument: gauge
Unit: Cel
"""


def create_hw_host_ambient_temperature(
    meter: Meter, callbacks: Optional[Sequence[CallbackT]]
) -> ObservableGauge:
    """Ambient (external) temperature of the physical host"""
    return meter.create_observable_gauge(
        name=HW_HOST_AMBIENT_TEMPERATURE,
        callbacks=callbacks,
        description="Ambient (external) temperature of the physical host.",
        unit="Cel",
    )


HW_HOST_ENERGY: Final = "hw.host.energy"
"""
Total energy consumed by the entire physical host, in joules
Instrument: counter
Unit: J
Note: The overall energy usage of a host MUST be reported using the specific `hw.host.energy` and `hw.host.power` metrics **only**, instead of the generic `hw.energy` and `hw.power` described in the previous section, to prevent summing up overlapping values.
"""


def create_hw_host_energy(meter: Meter) -> Counter:
    """Total energy consumed by the entire physical host, in joules"""
    return meter.create_counter(
        name=HW_HOST_ENERGY,
        description="Total energy consumed by the entire physical host, in joules.",
        unit="J",
    )


HW_HOST_HEATING_MARGIN: Final = "hw.host.heating_margin"
"""
By how many degrees Celsius the temperature of the physical host can be increased, before reaching a warning threshold on one of the internal sensors
Instrument: gauge
Unit: Cel
"""


def create_hw_host_heating_margin(
    meter: Meter, callbacks: Optional[Sequence[CallbackT]]
) -> ObservableGauge:
    """By how many degrees Celsius the temperature of the physical host can be increased, before reaching a warning threshold on one of the internal sensors"""
    return meter.create_observable_gauge(
        name=HW_HOST_HEATING_MARGIN,
        callbacks=callbacks,
        description="By how many degrees Celsius the temperature of the physical host can be increased, before reaching a warning threshold on one of the internal sensors.",
        unit="Cel",
    )


HW_HOST_POWER: Final = "hw.host.power"
"""
Instantaneous power consumed by the entire physical host in Watts (`hw.host.energy` is preferred)
Instrument: gauge
Unit: W
Note: The overall energy usage of a host MUST be reported using the specific `hw.host.energy` and `hw.host.power` metrics **only**, instead of the generic `hw.energy` and `hw.power` described in the previous section, to prevent summing up overlapping values.
"""


def create_hw_host_power(
    meter: Meter, callbacks: Optional[Sequence[CallbackT]]
) -> ObservableGauge:
    """Instantaneous power consumed by the entire physical host in Watts (`hw.host.energy` is preferred)"""
    return meter.create_observable_gauge(
        name=HW_HOST_POWER,
        callbacks=callbacks,
        description="Instantaneous power consumed by the entire physical host in Watts (`hw.host.energy` is preferred).",
        unit="W",
    )


HW_LOGICAL_DISK_LIMIT: Final = "hw.logical_disk.limit"
"""
Size of the logical disk
Instrument: updowncounter
Unit: By
"""


def create_hw_logical_disk_limit(meter: Meter) -> UpDownCounter:
    """Size of the logical disk"""
    return meter.create_up_down_counter(
        name=HW_LOGICAL_DISK_LIMIT,
        description="Size of the logical disk.",
        unit="By",
    )


HW_LOGICAL_DISK_USAGE: Final = "hw.logical_disk.usage"
"""
Logical disk space usage
Instrument: updowncounter
Unit: By
"""


def create_hw_logical_disk_usage(meter: Meter) -> UpDownCounter:
    """Logical disk space usage"""
    return meter.create_up_down_counter(
        name=HW_LOGICAL_DISK_USAGE,
        description="Logical disk space usage.",
        unit="By",
    )


HW_LOGICAL_DISK_UTILIZATION: Final = "hw.logical_disk.utilization"
"""
Logical disk space utilization as a fraction
Instrument: gauge
Unit: 1
"""


def create_hw_logical_disk_utilization(
    meter: Meter, callbacks: Optional[Sequence[CallbackT]]
) -> ObservableGauge:
    """Logical disk space utilization as a fraction"""
    return meter.create_observable_gauge(
        name=HW_LOGICAL_DISK_UTILIZATION,
        callbacks=callbacks,
        description="Logical disk space utilization as a fraction.",
        unit="1",
    )


HW_MEMORY_SIZE: Final = "hw.memory.size"
"""
Size of the memory module
Instrument: updowncounter
Unit: By
"""


def create_hw_memory_size(meter: Meter) -> UpDownCounter:
    """Size of the memory module"""
    return meter.create_up_down_counter(
        name=HW_MEMORY_SIZE,
        description="Size of the memory module.",
        unit="By",
    )


HW_NETWORK_BANDWIDTH_LIMIT: Final = "hw.network.bandwidth.limit"
"""
Link speed
Instrument: updowncounter
Unit: By/s
"""


def create_hw_network_bandwidth_limit(meter: Meter) -> UpDownCounter:
    """Link speed"""
    return meter.create_up_down_counter(
        name=HW_NETWORK_BANDWIDTH_LIMIT,
        description="Link speed.",
        unit="By/s",
    )


HW_NETWORK_BANDWIDTH_UTILIZATION: Final = "hw.network.bandwidth.utilization"
"""
Utilization of the network bandwidth as a fraction
Instrument: gauge
Unit: 1
"""


def create_hw_network_bandwidth_utilization(
    meter: Meter, callbacks: Optional[Sequence[CallbackT]]
) -> ObservableGauge:
    """Utilization of the network bandwidth as a fraction"""
    return meter.create_observable_gauge(
        name=HW_NETWORK_BANDWIDTH_UTILIZATION,
        callbacks=callbacks,
        description="Utilization of the network bandwidth as a fraction.",
        unit="1",
    )


HW_NETWORK_IO: Final = "hw.network.io"
"""
Received and transmitted network traffic in bytes
Instrument: counter
Unit: By
"""


def create_hw_network_io(meter: Meter) -> Counter:
    """Received and transmitted network traffic in bytes"""
    return meter.create_counter(
        name=HW_NETWORK_IO,
        description="Received and transmitted network traffic in bytes.",
        unit="By",
    )


HW_NETWORK_PACKETS: Final = "hw.network.packets"
"""
Received and transmitted network traffic in packets (or frames)
Instrument: counter
Unit: {packet}
"""


def create_hw_network_packets(meter: Meter) -> Counter:
    """Received and transmitted network traffic in packets (or frames)"""
    return meter.create_counter(
        name=HW_NETWORK_PACKETS,
        description="Received and transmitted network traffic in packets (or frames).",
        unit="{packet}",
    )


HW_NETWORK_UP: Final = "hw.network.up"
"""
Link status: `1` (up) or `0` (down)
Instrument: updowncounter
Unit: 1
"""


def create_hw_network_up(meter: Meter) -> UpDownCounter:
    """Link status: `1` (up) or `0` (down)"""
    return meter.create_up_down_counter(
        name=HW_NETWORK_UP,
        description="Link status: `1` (up) or `0` (down).",
        unit="1",
    )


HW_PHYSICAL_DISK_ENDURANCE_UTILIZATION: Final = (
    "hw.physical_disk.endurance_utilization"
)
"""
Endurance remaining for this SSD disk
Instrument: gauge
Unit: 1
"""


def create_hw_physical_disk_endurance_utilization(
    meter: Meter, callbacks: Optional[Sequence[CallbackT]]
) -> ObservableGauge:
    """Endurance remaining for this SSD disk"""
    return meter.create_observable_gauge(
        name=HW_PHYSICAL_DISK_ENDURANCE_UTILIZATION,
        callbacks=callbacks,
        description="Endurance remaining for this SSD disk.",
        unit="1",
    )


HW_PHYSICAL_DISK_SIZE: Final = "hw.physical_disk.size"
"""
Size of the disk
Instrument: updowncounter
Unit: By
"""


def create_hw_physical_disk_size(meter: Meter) -> UpDownCounter:
    """Size of the disk"""
    return meter.create_up_down_counter(
        name=HW_PHYSICAL_DISK_SIZE,
        description="Size of the disk.",
        unit="By",
    )


HW_PHYSICAL_DISK_SMART: Final = "hw.physical_disk.smart"
"""
Value of the corresponding [S.M.A.R.T.](https://wikipedia.org/wiki/S.M.A.R.T.) (Self-Monitoring, Analysis, and Reporting Technology) attribute
Instrument: gauge
Unit: 1
"""


def create_hw_physical_disk_smart(
    meter: Meter, callbacks: Optional[Sequence[CallbackT]]
) -> ObservableGauge:
    """Value of the corresponding [S.M.A.R.T.](https://wikipedia.org/wiki/S.M.A.R.T.) (Self-Monitoring, Analysis, and Reporting Technology) attribute"""
    return meter.create_observable_gauge(
        name=HW_PHYSICAL_DISK_SMART,
        callbacks=callbacks,
        description="Value of the corresponding [S.M.A.R.T.](https://wikipedia.org/wiki/S.M.A.R.T.) (Self-Monitoring, Analysis, and Reporting Technology) attribute.",
        unit="1",
    )


HW_POWER: Final = "hw.power"
"""
Instantaneous power consumed by the component
Instrument: gauge
Unit: W
Note: It is recommended to report `hw.energy` instead of `hw.power` when possible.
"""


def create_hw_power(
    meter: Meter, callbacks: Optional[Sequence[CallbackT]]
) -> ObservableGauge:
    """Instantaneous power consumed by the component"""
    return meter.create_observable_gauge(
        name=HW_POWER,
        callbacks=callbacks,
        description="Instantaneous power consumed by the component.",
        unit="W",
    )


HW_POWER_SUPPLY_LIMIT: Final = "hw.power_supply.limit"
"""
Maximum power output of the power supply
Instrument: updowncounter
Unit: W
"""


def create_hw_power_supply_limit(meter: Meter) -> UpDownCounter:
    """Maximum power output of the power supply"""
    return meter.create_up_down_counter(
        name=HW_POWER_SUPPLY_LIMIT,
        description="Maximum power output of the power supply.",
        unit="W",
    )


HW_POWER_SUPPLY_USAGE: Final = "hw.power_supply.usage"
"""
Current power output of the power supply
Instrument: updowncounter
Unit: W
"""


def create_hw_power_supply_usage(meter: Meter) -> UpDownCounter:
    """Current power output of the power supply"""
    return meter.create_up_down_counter(
        name=HW_POWER_SUPPLY_USAGE,
        description="Current power output of the power supply.",
        unit="W",
    )


HW_POWER_SUPPLY_UTILIZATION: Final = "hw.power_supply.utilization"
"""
Utilization of the power supply as a fraction of its maximum output
Instrument: gauge
Unit: 1
"""


def create_hw_power_supply_utilization(
    meter: Meter, callbacks: Optional[Sequence[CallbackT]]
) -> ObservableGauge:
    """Utilization of the power supply as a fraction of its maximum output"""
    return meter.create_observable_gauge(
        name=HW_POWER_SUPPLY_UTILIZATION,
        callbacks=callbacks,
        description="Utilization of the power supply as a fraction of its maximum output.",
        unit="1",
    )


HW_STATUS: Final = "hw.status"
"""
Operational status: `1` (true) or `0` (false) for each of the possible states
Instrument: updowncounter
Unit: 1
Note: `hw.status` is currently specified as an *UpDownCounter* but would ideally be represented using a [*StateSet* as defined in OpenMetrics](https://github.com/prometheus/OpenMetrics/blob/v1.0.0/specification/OpenMetrics.md#stateset). This semantic convention will be updated once *StateSet* is specified in OpenTelemetry. This planned change is not expected to have any consequence on the way users query their timeseries backend to retrieve the values of `hw.status` over time.
"""


def create_hw_status(meter: Meter) -> UpDownCounter:
    """Operational status: `1` (true) or `0` (false) for each of the possible states"""
    return meter.create_up_down_counter(
        name=HW_STATUS,
        description="Operational status: `1` (true) or `0` (false) for each of the possible states.",
        unit="1",
    )


HW_TAPE_DRIVE_OPERATIONS: Final = "hw.tape_drive.operations"
"""
Operations performed by the tape drive
Instrument: counter
Unit: {operation}
"""


def create_hw_tape_drive_operations(meter: Meter) -> Counter:
    """Operations performed by the tape drive"""
    return meter.create_counter(
        name=HW_TAPE_DRIVE_OPERATIONS,
        description="Operations performed by the tape drive.",
        unit="{operation}",
    )


HW_TEMPERATURE: Final = "hw.temperature"
"""
Temperature in degrees Celsius
Instrument: gauge
Unit: Cel
"""


def create_hw_temperature(
    meter: Meter, callbacks: Optional[Sequence[CallbackT]]
) -> ObservableGauge:
    """Temperature in degrees Celsius"""
    return meter.create_observable_gauge(
        name=HW_TEMPERATURE,
        callbacks=callbacks,
        description="Temperature in degrees Celsius.",
        unit="Cel",
    )


HW_TEMPERATURE_LIMIT: Final = "hw.temperature.limit"
"""
Temperature limit in degrees Celsius
Instrument: gauge
Unit: Cel
"""


def create_hw_temperature_limit(
    meter: Meter, callbacks: Optional[Sequence[CallbackT]]
) -> ObservableGauge:
    """Temperature limit in degrees Celsius"""
    return meter.create_observable_gauge(
        name=HW_TEMPERATURE_LIMIT,
        callbacks=callbacks,
        description="Temperature limit in degrees Celsius.",
        unit="Cel",
    )


HW_VOLTAGE: Final = "hw.voltage"
"""
Voltage measured by the sensor
Instrument: gauge
Unit: V
"""


def create_hw_voltage(
    meter: Meter, callbacks: Optional[Sequence[CallbackT]]
) -> ObservableGauge:
    """Voltage measured by the sensor"""
    return meter.create_observable_gauge(
        name=HW_VOLTAGE,
        callbacks=callbacks,
        description="Voltage measured by the sensor.",
        unit="V",
    )


HW_VOLTAGE_LIMIT: Final = "hw.voltage.limit"
"""
Voltage limit in Volts
Instrument: gauge
Unit: V
"""


def create_hw_voltage_limit(
    meter: Meter, callbacks: Optional[Sequence[CallbackT]]
) -> ObservableGauge:
    """Voltage limit in Volts"""
    return meter.create_observable_gauge(
        name=HW_VOLTAGE_LIMIT,
        callbacks=callbacks,
        description="Voltage limit in Volts.",
        unit="V",
    )


HW_VOLTAGE_NOMINAL: Final = "hw.voltage.nominal"
"""
Nominal (expected) voltage
Instrument: gauge
Unit: V
"""


def create_hw_voltage_nominal(
    meter: Meter, callbacks: Optional[Sequence[CallbackT]]
) -> ObservableGauge:
    """Nominal (expected) voltage"""
    return meter.create_observable_gauge(
        name=HW_VOLTAGE_NOMINAL,
        callbacks=callbacks,
        description="Nominal (expected) voltage.",
        unit="V",
    )
