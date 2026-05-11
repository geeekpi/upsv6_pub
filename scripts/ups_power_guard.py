#!/usr/bin/env python3
"""Graceful power-loss guard for the 52Pi / GeekPi UPS V6 HAT.

This daemon watches UPS telemetry over I2C and coordinates a controlled
service stop and eventual system poweroff when external power is lost.
"""

from __future__ import annotations

import json
import logging
import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Sequence

from smbus2 import SMBus


INPUT_VOLTAGE_REG = 0x10
BATTERY_VOLTAGE_REG = 0x12
INPUT_CURRENT_REG = 0x18
BATTERY_CURRENT_REG = 0x1A

DEFAULT_I2C_BUS = 1
DEFAULT_I2C_ADDRESS = 0x17
DEFAULT_INPUT_PRESENT_MV = 4500
DEFAULT_BATTERY_SHUTDOWN_MV = 7600
DEFAULT_POWER_LOSS_DEBOUNCE_SEC = 8
DEFAULT_MAX_OUTAGE_RUNTIME_SEC = 180
DEFAULT_POLL_SEC = 2.0

STOP_COMMAND_TIMEOUT_SEC = 90
START_COMMAND_TIMEOUT_SEC = 60
SYNC_TIMEOUT_SEC = 30
POWEROFF_TIMEOUT_SEC = 30


class GuardError(Exception):
    """Raised for configuration or runtime guard issues."""


@dataclass(frozen=True)
class GuardConfig:
    i2c_bus: int
    i2c_address: int
    input_present_mv: int
    battery_shutdown_mv: int
    power_loss_debounce_sec: float
    max_outage_runtime_sec: float
    poll_sec: float
    stop_commands: list[list[str]]
    start_commands: list[list[str]]
    log_file: str | None


@dataclass(frozen=True)
class Telemetry:
    input_voltage_mv: int
    battery_voltage_mv: int
    input_current_ma: int
    battery_current_ma: int


@dataclass
class GuardState:
    power_loss_started_monotonic: float | None = None
    outage_confirmed_monotonic: float | None = None
    services_stopped_by_guard: bool = False
    stop_phase_complete: bool = False
    shutdown_requested: bool = False
    last_power_present: bool | None = None
    stop_reason: str | None = None


LOGGER = logging.getLogger("ups_power_guard")
SHUTDOWN_SIGNAL_RECEIVED = False


def configure_bootstrap_logging() -> None:
    if LOGGER.handlers:
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    LOGGER.setLevel(logging.INFO)
    LOGGER.addHandler(handler)
    LOGGER.propagate = False


def parse_env_int(name: str, default: int) -> int:
    value = os.environ.get(name)
    if value is None or value.strip() == "":
        return default
    try:
        return int(value, 0)
    except ValueError as exc:
        raise GuardError(f"{name} must be an integer, got {value!r}") from exc


def parse_env_float(name: str, default: float) -> float:
    value = os.environ.get(name)
    if value is None or value.strip() == "":
        return default
    try:
        return float(value)
    except ValueError as exc:
        raise GuardError(f"{name} must be numeric, got {value!r}") from exc


def parse_command_env(name: str) -> list[list[str]]:
    value = os.environ.get(name)
    if value is None or value.strip() == "":
        return []

    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        LOGGER.exception("%s is not valid JSON; ignoring configured commands", name)
        return []

    if not isinstance(parsed, list):
        LOGGER.error("%s must be a JSON array of command arrays; ignoring it", name)
        return []

    commands: list[list[str]] = []
    for index, item in enumerate(parsed):
        if not isinstance(item, list) or not item:
            LOGGER.error(
                "%s entry %s must be a non-empty JSON array; ignoring that entry",
                name,
                index,
            )
            continue
        if not all(isinstance(part, str) and part for part in item):
            LOGGER.error(
                "%s entry %s must contain only non-empty strings; ignoring that entry",
                name,
                index,
            )
            continue
        commands.append(item)

    return commands


def load_config() -> GuardConfig:
    return GuardConfig(
        i2c_bus=parse_env_int("UPS_I2C_BUS", DEFAULT_I2C_BUS),
        i2c_address=parse_env_int("UPS_I2C_ADDRESS", DEFAULT_I2C_ADDRESS),
        input_present_mv=parse_env_int(
            "UPS_INPUT_PRESENT_MV", DEFAULT_INPUT_PRESENT_MV
        ),
        battery_shutdown_mv=parse_env_int(
            "UPS_BATTERY_SHUTDOWN_MV", DEFAULT_BATTERY_SHUTDOWN_MV
        ),
        power_loss_debounce_sec=parse_env_float(
            "UPS_POWER_LOSS_DEBOUNCE_SEC", DEFAULT_POWER_LOSS_DEBOUNCE_SEC
        ),
        max_outage_runtime_sec=parse_env_float(
            "UPS_MAX_OUTAGE_RUNTIME_SEC", DEFAULT_MAX_OUTAGE_RUNTIME_SEC
        ),
        poll_sec=parse_env_float("UPS_POLL_SEC", DEFAULT_POLL_SEC),
        stop_commands=parse_command_env("UPS_STOP_COMMANDS"),
        start_commands=parse_command_env("UPS_START_COMMANDS"),
        log_file=os.environ.get("UPS_LOG_FILE") or None,
    )


def configure_logging(log_file: str | None) -> None:
    LOGGER.setLevel(logging.INFO)
    LOGGER.handlers.clear()
    LOGGER.propagate = False

    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)
    LOGGER.addHandler(stdout_handler)

    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        LOGGER.addHandler(file_handler)


def handle_shutdown_signal(signum: int, _frame: object) -> None:
    global SHUTDOWN_SIGNAL_RECEIVED
    SHUTDOWN_SIGNAL_RECEIVED = True
    LOGGER.info("Received signal %s; exiting after current loop", signum)


def read_register(bus: SMBus, address: int, register: int) -> int:
    """Read a signed 16-bit register value in the vendor's raw mV/mA format."""
    value = bus.read_word_data(address, register)
    if value > 32767:
        value -= 65536
    return value


def read_telemetry(bus: SMBus, config: GuardConfig) -> Telemetry:
    return Telemetry(
        input_voltage_mv=read_register(bus, config.i2c_address, INPUT_VOLTAGE_REG),
        battery_voltage_mv=read_register(bus, config.i2c_address, BATTERY_VOLTAGE_REG),
        input_current_ma=read_register(bus, config.i2c_address, INPUT_CURRENT_REG),
        battery_current_ma=read_register(bus, config.i2c_address, BATTERY_CURRENT_REG),
    )


def external_power_present(input_voltage_mv: int, threshold_mv: int) -> bool:
    return input_voltage_mv >= threshold_mv


def run_commands(
    commands: Sequence[Sequence[str]],
    action_name: str,
    timeout_sec: int,
) -> bool:
    if not commands:
        LOGGER.info("%s: no commands configured", action_name)
        return True

    overall_success = True
    for command in commands:
        try:
            LOGGER.info("%s: running command: %s", action_name, command)
            completed = subprocess.run(
                list(command),
                capture_output=True,
                text=True,
                timeout=timeout_sec,
                check=False,
            )
        except FileNotFoundError:
            LOGGER.exception("%s: executable not found for command %s", action_name, command)
            overall_success = False
            continue
        except subprocess.TimeoutExpired:
            LOGGER.exception("%s: command timed out after %ss: %s", action_name, timeout_sec, command)
            overall_success = False
            continue
        except Exception:
            LOGGER.exception("%s: unexpected failure running command %s", action_name, command)
            overall_success = False
            continue

        stdout = completed.stdout.strip()
        stderr = completed.stderr.strip()
        if stdout:
            LOGGER.info("%s stdout: %s", action_name, stdout)
        if stderr:
            LOGGER.warning("%s stderr: %s", action_name, stderr)

        if completed.returncode != 0:
            LOGGER.error(
                "%s: command failed with exit code %s: %s",
                action_name,
                completed.returncode,
                command,
            )
            overall_success = False
        else:
            LOGGER.info("%s: command completed successfully: %s", action_name, command)

    return overall_success


def stop_services(config: GuardConfig, state: GuardState, reason: str) -> bool:
    if state.stop_phase_complete:
        LOGGER.info(
            "Service stop already completed earlier in this outage; reason=%s original_reason=%s",
            reason,
            state.stop_reason,
        )
        return True

    LOGGER.warning("Stopping protected services due to %s", reason)
    success = run_commands(config.stop_commands, "stop_services", STOP_COMMAND_TIMEOUT_SEC)
    state.stop_phase_complete = True
    state.services_stopped_by_guard = success and bool(config.stop_commands)
    state.stop_reason = reason

    if success:
        LOGGER.info(
            "Protected service stop phase completed; services_stopped_by_guard=%s",
            state.services_stopped_by_guard,
        )
    else:
        LOGGER.error(
            "Protected service stop phase completed with failures; automatic restart on restore is disabled"
        )
    return success


def start_services(config: GuardConfig, state: GuardState) -> bool:
    if not state.services_stopped_by_guard:
        LOGGER.info("Skipping service restart because this daemon did not stop any services")
        return True

    LOGGER.info("External power restored; restarting protected services")
    success = run_commands(config.start_commands, "start_services", START_COMMAND_TIMEOUT_SEC)
    if success:
        state.services_stopped_by_guard = False
        state.stop_phase_complete = False
        state.stop_reason = None
        LOGGER.info("Protected services restarted successfully")
    else:
        LOGGER.error("Protected service restart completed with failures")
    return success


def sync_filesystems() -> bool:
    LOGGER.info("Syncing filesystems")
    return run_commands((["sync"],), "sync_filesystems", SYNC_TIMEOUT_SEC)


def poweroff(state: GuardState, reason: str) -> None:
    if state.shutdown_requested:
        LOGGER.info("Poweroff already requested earlier; reason=%s", reason)
        return

    state.shutdown_requested = True
    LOGGER.critical("Requesting system poweroff due to %s", reason)
    run_commands((["systemctl", "poweroff"],), "poweroff", POWEROFF_TIMEOUT_SEC)


def open_bus(config: GuardConfig) -> SMBus:
    LOGGER.info("Opening I2C bus %s at address 0x%02x", config.i2c_bus, config.i2c_address)
    return SMBus(config.i2c_bus)


def reset_for_power_restore(state: GuardState) -> None:
    state.power_loss_started_monotonic = None
    state.outage_confirmed_monotonic = None
    state.stop_phase_complete = False
    state.stop_reason = None


def log_telemetry(telemetry: Telemetry, power_present: bool, state: GuardState) -> None:
    outage_duration = (
        time.monotonic() - state.outage_confirmed_monotonic
        if state.outage_confirmed_monotonic is not None
        else 0.0
    )
    LOGGER.info(
        "telemetry input_mv=%s battery_mv=%s input_ma=%s battery_ma=%s external_power=%s services_stopped=%s outage_sec=%.1f",
        telemetry.input_voltage_mv,
        telemetry.battery_voltage_mv,
        telemetry.input_current_ma,
        telemetry.battery_current_ma,
        power_present,
        state.services_stopped_by_guard,
        outage_duration,
    )


def main() -> int:
    configure_bootstrap_logging()
    config = load_config()
    configure_logging(config.log_file)

    signal.signal(signal.SIGINT, handle_shutdown_signal)
    signal.signal(signal.SIGTERM, handle_shutdown_signal)

    LOGGER.info(
        "Starting UPS power guard with bus=%s address=0x%02x input_present_mv=%s battery_shutdown_mv=%s debounce_sec=%s max_outage_runtime_sec=%s poll_sec=%s",
        config.i2c_bus,
        config.i2c_address,
        config.input_present_mv,
        config.battery_shutdown_mv,
        config.power_loss_debounce_sec,
        config.max_outage_runtime_sec,
        config.poll_sec,
    )

    bus: SMBus | None = None
    state = GuardState()

    # State machine:
    # - AC_OK: power present, services running.
    # - AC_LOSS_PENDING: input below threshold, debounce in progress.
    # - ON_BATTERY_SERVICES_STOPPED: outage confirmed, services stopped and synced.
    # - SHUTDOWN_REQUESTED: poweroff already requested; avoid duplicate actions.
    while not SHUTDOWN_SIGNAL_RECEIVED:
        if bus is None:
            try:
                bus = open_bus(config)
            except Exception:
                LOGGER.exception("Unable to open I2C bus; retrying")
                time.sleep(config.poll_sec)
                continue

        try:
            telemetry = read_telemetry(bus, config)
        except Exception:
            LOGGER.exception("UPS telemetry read failed; will retry without inferring power state")
            try:
                bus.close()
            except Exception:
                LOGGER.exception("Failed to close I2C bus after read error")
            bus = None
            time.sleep(config.poll_sec)
            continue

        power_present = external_power_present(
            telemetry.input_voltage_mv,
            config.input_present_mv,
        )
        log_telemetry(telemetry, power_present, state)

        if power_present:
            if state.last_power_present is False:
                LOGGER.info("External power is present again")
            restart_ok = True
            if state.services_stopped_by_guard:
                restart_ok = start_services(config, state)
            if restart_ok:
                reset_for_power_restore(state)
            state.last_power_present = True
            time.sleep(config.poll_sec)
            continue

        now = time.monotonic()
        if state.last_power_present is not False:
            LOGGER.warning(
                "External power loss detected: input voltage %smV is below threshold %smV",
                telemetry.input_voltage_mv,
                config.input_present_mv,
            )
        state.last_power_present = False

        if state.power_loss_started_monotonic is None:
            state.power_loss_started_monotonic = now
            LOGGER.info(
                "Starting power-loss debounce timer for %.1fs",
                config.power_loss_debounce_sec,
            )

        if state.outage_confirmed_monotonic is None:
            elapsed = now - state.power_loss_started_monotonic
            if elapsed >= config.power_loss_debounce_sec:
                state.outage_confirmed_monotonic = now
                LOGGER.warning(
                    "External power loss confirmed after %.1fs on battery",
                    elapsed,
                )
                stop_services(config, state, "external power loss")
                sync_filesystems()
            else:
                time.sleep(config.poll_sec)
                continue

        outage_runtime = now - state.outage_confirmed_monotonic
        if telemetry.battery_voltage_mv < config.battery_shutdown_mv:
            LOGGER.critical(
                "Battery voltage %smV is below shutdown threshold %smV",
                telemetry.battery_voltage_mv,
                config.battery_shutdown_mv,
            )
            stop_services(config, state, "low battery")
            sync_filesystems()
            poweroff(state, "low battery")
        elif outage_runtime >= config.max_outage_runtime_sec:
            LOGGER.critical(
                "Outage runtime %.1fs exceeded limit %.1fs",
                outage_runtime,
                config.max_outage_runtime_sec,
            )
            stop_services(config, state, "outage runtime exceeded")
            sync_filesystems()
            poweroff(state, "outage runtime exceeded")

        time.sleep(config.poll_sec)

    if bus is not None:
        try:
            bus.close()
        except Exception:
            LOGGER.exception("Failed to close I2C bus during shutdown")

    LOGGER.info("UPS power guard exiting")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except GuardError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
