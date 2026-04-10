# Timewarrior Projected vs Actual Script Change Log

## [1.2] - pending

### Change
*   **Script Rename:** Renamed the script from analysis.py to projected.py to naming consistency.


## [1.1] - 2026-04-08 

### Added
*   **Tag Exclusion:** Added the ability to ignore time segments with specific tags. This can be configured via `projected.ignore_tags` in the Timewarrior config or passed directly at runtime using the `--ignore` CLI argument.
*   **Excluded Time Summary:** Added an optional summary block at the end of the report to display totals for excluded tags (toggleable via the `projected.summarize_excluded` config option).
*   **Terminal Colors:** Introduced ANSI color formatting (RGB125) to highlight excluded tags in the output header and summary.
*   **CLI Argument Parsing:** Integrated `argparse` to gracefully handle command-line options alongside piped standard input.

### Changed
*   **Timezone Handling:** Updated the open-interval end time calculation in `parse_time_entries` to use timezone-aware `datetime.now(timezone.utc)` instead of the deprecated `datetime.utcnow()`.
*   **Date Range Logic:** Refactored the date range generation directly into `main()`, removing the standalone `get_date_range()` function to better support the new beginning-of-month baseline logic.

### Fixed
*   **Beginning of Month Bug:** Fixed an issue where days early in the month without logged entries were omitted from the total projected time calculation. The script now snaps the start date to the 1st of the month of the earliest entry and ensures the range extends to the current date.

## [1.0] - 2026-02-08

### Added
*   Initial release of the analysis script (a.k.a projected).
