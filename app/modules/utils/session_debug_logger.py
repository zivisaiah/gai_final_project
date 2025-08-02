"""
Session Debug Logger
Captures comprehensive debug information during Streamlit sessions for export
"""

import json
import logging
import sys
import io
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class DebugLogEntry:
    """Single debug log entry"""

    timestamp: str
    level: str
    component: str
    action: str
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


class SessionDebugLogger:
    """Comprehensive debug logger for Streamlit sessions"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.debug_entries: List[DebugLogEntry] = []
        self.session_start_time = datetime.now()
        self.console_logs: List[str] = []

        # Setup file logging
        self.log_dir = Path("data/debug_logs")
        self.log_dir.mkdir(exist_ok=True)
        self.log_file = self.log_dir / f"session_{session_id}.log"
        self.console_log_file = self.log_dir / f"console_{session_id}.log"

        # Setup file handler
        self.file_handler = logging.FileHandler(self.log_file)
        self.file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )

        # Setup console capture
        self.setup_console_capture()

        self.log_session_start()

    def setup_console_capture(self):
        """Setup console output capture"""
        try:
            # Create a custom stream that captures both stdout and logs
            class ConsoleCapture:
                def __init__(self, original_stream, logger):
                    self.original_stream = original_stream
                    self.logger = logger

                def write(self, text):
                    # Write to original stream
                    self.original_stream.write(text)
                    # Capture in logger
                    if text.strip():  # Only capture non-empty lines
                        # Enhanced microsecond precision for timing analysis
                        timestamp = datetime.now().strftime("%H:%M:%S.%f")[
                            :-3
                        ]  # Keep 3 decimal places
                        self.logger.console_logs.append(f"[{timestamp}] {text.strip()}")

                        # Also write to console log file
                        with open(self.logger.console_log_file, "a") as f:
                            f.write(f"[{timestamp}] {text}")

                def flush(self):
                    self.original_stream.flush()

            # Replace stdout and stderr with capturing versions
            self.original_stdout = sys.stdout
            self.original_stderr = sys.stderr
            sys.stdout = ConsoleCapture(self.original_stdout, self)
            sys.stderr = ConsoleCapture(self.original_stderr, self)

        except Exception as e:
            # If console capture fails, just log the error and continue
            self.log_debug(
                "console_capture", "setup_failed", {"error": str(e)}, "WARNING"
            )

    def restore_console(self):
        """Restore original console streams"""
        try:
            if hasattr(self, "original_stdout"):
                sys.stdout = self.original_stdout
            if hasattr(self, "original_stderr"):
                sys.stderr = self.original_stderr
        except Exception as e:
            pass

    def log_session_start(self):
        """Log session initialization"""
        self.log_debug(
            component="session",
            action="session_start",
            data={
                "session_id": self.session_id,
                "start_time": self.session_start_time.isoformat(),
            },
        )

    def log_debug(
        self,
        component: str,
        action: str,
        data: Dict[str, Any],
        level: str = "INFO",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Log a debug entry with microsecond precision"""
        # Enhanced timestamp with microseconds for precise timing analysis
        now = datetime.now()
        precise_timestamp = now.strftime("%Y-%m-%dT%H:%M:%S.%f")[
            :-3
        ]  # Keep 3 decimal places

        entry = DebugLogEntry(
            timestamp=precise_timestamp,
            level=level,
            component=component,
            action=action,
            data=data.copy() if data else {},
            metadata=metadata.copy() if metadata else None,
        )

        self.debug_entries.append(entry)

        # Also log to file
        log_message = f"[{component}] {action}: {json.dumps(data, default=str)}"
        if metadata:
            log_message += f" | Metadata: {json.dumps(metadata, default=str)}"

        # Get logger for this component
        logger = logging.getLogger(f"session_debug.{component}")
        logger.addHandler(self.file_handler)

        if level == "ERROR":
            logger.error(log_message)
        elif level == "WARNING":
            logger.warning(log_message)
        else:
            logger.info(log_message)

    def log_user_input(self, message: str, metadata: Optional[Dict] = None):
        """Log user input"""
        self.log_debug(
            component="user_input",
            action="message_received",
            data={"message": message},
            metadata=metadata,
        )

    def log_agent_decision(
        self, decision: str, reasoning: str, metadata: Optional[Dict] = None
    ):
        """Log agent decision"""
        self.log_debug(
            component="core_agent",
            action="decision_made",
            data={"decision": decision, "reasoning": reasoning},
            metadata=metadata,
        )

    def log_slot_offering(self, slots: List[Dict], metadata: Optional[Dict] = None):
        """Log when slots are offered to user"""
        slots_data = []
        for i, slot in enumerate(slots):
            if hasattr(slot, "id"):
                # AvailableSlotResponse object
                slot_data = {
                    "index": i,
                    "id": slot.id,
                    "recruiter": slot.recruiter.name
                    if hasattr(slot, "recruiter") and slot.recruiter
                    else "Unknown",
                    "recruiter_id": slot.recruiter_id,
                    "datetime": f"{slot.slot_date} {slot.start_time}",
                    "is_available": slot.is_available,
                }
            else:
                # Dictionary format
                slot_data = {
                    "index": i,
                    "id": slot.get("id"),
                    "recruiter": slot.get("recruiter"),
                    "recruiter_id": slot.get("recruiter_id"),
                    "datetime": slot.get("datetime"),
                    "is_available": slot.get("is_available", True),
                }
            slots_data.append(slot_data)

        self.log_debug(
            component="scheduling",
            action="slots_offered",
            data={"total_slots": len(slots), "slots": slots_data},
            metadata=metadata,
        )

    def log_slot_selection(
        self,
        selected_slot: Dict,
        user_action: str = "button_click",
        metadata: Optional[Dict] = None,
    ):
        """Log when user selects a slot"""
        self.log_debug(
            component="slot_selection",
            action="slot_selected",
            data={
                "user_action": user_action,
                "selected_slot": selected_slot,
                "slot_id": selected_slot.get("id"),
                "recruiter": selected_slot.get("recruiter"),
                "datetime": selected_slot.get("datetime"),
            },
            metadata=metadata,
        )

    def log_slot_confirmation_flow(
        self, stage: str, data: Dict[str, Any], metadata: Optional[Dict] = None
    ):
        """Log slot confirmation flow stages"""
        self.log_debug(
            component="slot_confirmation",
            action=f"stage_{stage}",
            data=data,
            metadata=metadata,
        )

    def log_database_operation(
        self,
        operation: str,
        data: Dict[str, Any],
        result: Optional[Dict] = None,
        metadata: Optional[Dict] = None,
    ):
        """Log database operations"""
        log_data = {"operation": operation, "input": data}
        if result:
            log_data["result"] = result

        self.log_debug(
            component="database", action="operation", data=log_data, metadata=metadata
        )

    def log_booking_result(
        self, booking_result: Dict[str, Any], metadata: Optional[Dict] = None
    ):
        """Log final booking result"""
        self.log_debug(
            component="booking",
            action="booking_completed",
            data=booking_result,
            metadata=metadata,
        )

    def log_error(
        self,
        component: str,
        error: str,
        context: Dict[str, Any],
        exception: Optional[Exception] = None,
    ):
        """Log errors with context"""
        error_data = {"error_message": error, "context": context}

        if exception:
            error_data["exception_type"] = type(exception).__name__
            error_data["exception_str"] = str(exception)

        self.log_debug(
            component=component, action="error_occurred", data=error_data, level="ERROR"
        )

    def get_session_summary(self) -> Dict[str, Any]:
        """Get comprehensive session summary"""
        # Analyze the debug entries
        components = set(entry.component for entry in self.debug_entries)
        actions = set(entry.action for entry in self.debug_entries)
        errors = [entry for entry in self.debug_entries if entry.level == "ERROR"]

        # Extract key events
        slot_offerings = [
            entry
            for entry in self.debug_entries
            if entry.component == "scheduling" and entry.action == "slots_offered"
        ]
        slot_selections = [
            entry for entry in self.debug_entries if entry.component == "slot_selection"
        ]
        bookings = [
            entry for entry in self.debug_entries if entry.component == "booking"
        ]

        return {
            "session_info": {
                "session_id": self.session_id,
                "start_time": self.session_start_time.isoformat(),
                "duration_minutes": (
                    datetime.now() - self.session_start_time
                ).total_seconds()
                / 60,
                "total_entries": len(self.debug_entries),
            },
            "components_involved": sorted(list(components)),
            "actions_performed": sorted(list(actions)),
            "error_count": len(errors),
            "errors": [asdict(error) for error in errors],
            "key_events": {
                "slot_offerings": len(slot_offerings),
                "slot_selections": len(slot_selections),
                "booking_attempts": len(bookings),
            },
            "slot_flow_analysis": self._analyze_slot_flow(),
            "log_file_path": str(self.log_file),
        }

    def _analyze_slot_flow(self) -> Dict[str, Any]:
        """Analyze the slot selection flow for mismatches"""
        slot_offerings = [
            entry
            for entry in self.debug_entries
            if entry.component == "scheduling" and entry.action == "slots_offered"
        ]
        slot_selections = [
            entry for entry in self.debug_entries if entry.component == "slot_selection"
        ]
        bookings = [
            entry for entry in self.debug_entries if entry.component == "booking"
        ]

        analysis = {
            "offers_made": len(slot_offerings),
            "selections_made": len(slot_selections),
            "bookings_completed": len(bookings),
            "flow_issues": [],
        }

        # Check for mismatches
        if slot_selections and bookings:
            last_selection = slot_selections[-1]
            last_booking = bookings[-1]

            selected_recruiter = last_selection.data.get("recruiter")
            if last_booking.data.get("success"):
                booked_recruiter = last_booking.data.get("appointment_details", {}).get(
                    "recruiter"
                )

                if (
                    selected_recruiter
                    and booked_recruiter
                    and selected_recruiter != booked_recruiter
                ):
                    analysis["flow_issues"].append(
                        {
                            "type": "recruiter_mismatch",
                            "selected_recruiter": selected_recruiter,
                            "booked_recruiter": booked_recruiter,
                            "selection_timestamp": last_selection.timestamp,
                            "booking_timestamp": last_booking.timestamp,
                        }
                    )

        return analysis

    def export_debug_log(self) -> Dict[str, Any]:
        """Export complete debug log"""
        return {
            "session_summary": self.get_session_summary(),
            "complete_log": [asdict(entry) for entry in self.debug_entries],
            "console_logs": self.console_logs,
            "console_log_count": len(self.console_logs),
            "export_timestamp": datetime.now().isoformat(),
        }

    def save_debug_export(self, filename: Optional[str] = None) -> str:
        """Save debug export to file"""
        if not filename:
            filename = f"debug_export_{self.session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        export_path = self.log_dir / filename
        export_data = self.export_debug_log()

        with open(export_path, "w") as f:
            json.dump(export_data, f, indent=2, default=str)

        return str(export_path)
