# Sample operational data

`sample_operational_window.csv` contains a short, anonymized window from the full ThingSpeak export:

- Window: 2024-10-19 00:30:00 to 03:00:00 UTC
- Original fields retained: `field1`, `field3`, and `field6`
- The stream is asynchronous: most rows update one field while the other fields are blank.
- The window includes a recorded low-pressure (`3`) to high-pressure (`6`) transition.

Working interpretation:

- `field1`: likely main-tank stored-volume estimate; confirm from the original channel configuration.
- `field3`: primary monitored flow, L/min.
- `field6`: controller state code.

The full raw export is not included because it contains more than five million records and may retain infrastructure-specific identifiers.
