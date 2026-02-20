---

# Timewarrior Hours Analysis (`projected`)

A Python-based extension for [Timewarrior](https://timewarrior.net/) that provides a detailed daily breakdown of work hours, holiday handling, and "accumulated vs. projected" totals to help you stay on track with your goals.

---

## Features

* **Daily Breakdown:** Detailed view of hours worked versus daily goals.
* **Monthly Projections:** Tracks progress against a rolling target based on your specific schedule.
* **Holiday Aware:** Automatically adjusts goals for holidays based on your standard work day length.
* **Multi-Source Tag Filtering:** Exclude specific tags (e.g., `Lunch`, `SideQuest`) from total calculations. Tags can be defined in the script, in your `timewarrior.cfg`, or at runtime.
* **Excluded Time Summary:** Optional breakdown at the end of the report showing exactly how much time was "lost" to each ignored tag.
* **Timezone Aware:** Automatically converts UTC Timewarrior data to your local system time.
* **Visual Feedback:** Scannable week-by-week dividers and status indicators (▲ ahead / ▼ behind) using Timewarrior's `rgb125` theme color.

---

## Example Output

```text
Excluded tags: Lunch, SideQuest

Date               Goal       Worked     Day +/-    Total      Status
-----------------------------------------------------------------------
W01 Jan Mon 02     9:00       8:30       -0:30      8:30       -0:30 ▼
W01 Jan Tue 03     9:00       9:45       +0:45      18:15      +0:15 ▲
W01 Jan Wed 04     1:00       0:00       -1:00      18:15      -0:45 ▼  ← Holiday
W01 Jan Thu 05     9:00       9:10       +0:10      27:25      -0:35 ▼
-----------------------------------------------------------------------
Week 01 Summary:   28:00      27:25      (Behind goal by 0:35)

Excluded Time Summary:
------------------------------
Lunch              2:30
SideQuest          1:15

```

> [!IMPORTANT]
> **The "Extra Hour" Logic:** On holidays, the script calculates the difference between your `totals.hours_per_day` (e.g., 9h) and a standard 8h holiday credit. If you work a 9/80 schedule, the script will show a 1:00 goal on holidays to ensure your full period is covered.

---

## Installation & Setup

### 1. Link the Extension

Create a symbolic link in the Timewarrior extensions directory without the `.py` extension:

```bash
# Link the script
ln -s /path/to/your/repo/analysis.py ~/.timewarrior/extensions/projected
# Make it executable
chmod +x ~/.timewarrior/extensions/projected

```

### 2. Standard Configuration Template

Add this to your `~/.timewarrior/timewarrior.cfg`.

```ini
# --- Schedule (Exclusions define non-work time) ---
exclusions.monday:    <00:00 >09:00 <17:00 >24:00
exclusions.tuesday:   <00:00 >09:00 <17:00 >24:00
exclusions.wednesday: <00:00 >09:00 <17:00 >24:00
exclusions.thursday:  <00:00 >09:00 <17:00 >24:00
exclusions.friday:    <00:00 >09:00 <17:00 >24:00

# --- Targets & Holidays ---
# Set your standard workday length (used for holiday math)
totals.hours_per_day = 9.0

# --- Report Appearance ---
projected.show_weekends = no
projected.weekly_summary = yes

# --- Tag Filtering ---
# Tags to ignore (space-separated)
projected.ignore_tags = Lunch SideQuest Personal
# Show the 'Excluded Time Summary' at the bottom
projected.summarize_excluded = yes

# --- Holiday Calendar ---
holidays.US.2026-01-01: New Year's Day
holidays.US.2026-12-25: Christmas

```

### 3. Recommended Aliases

Add these to your `~/.bashrc` or `~/.zshrc` for quick access:

```bash
alias twp='timew projected :month'
alias twlp='timew projected :lastmonth'

```

---

## Usage

### Dynamic Tag Filtering

The script merges ignored tags from three sources:

1. **Script Defaults:** `DEFAULT_IGNORED_TAGS` in the Python file.
2. **Config file:** `projected.ignore_tags` in `timewarrior.cfg`.
3. **Runtime:** Using the `--ignore` flag.

```bash
# Ignore 'Meeting' just for this run
timew projected :month --ignore Meeting

```

---

## Troubleshooting

* **Goals show as 0:00:** Goals are calculated from the *gaps* in your `exclusions`. Check your `.cfg` for valid ranges.
* **Extension not found:** Ensure the symlink in `~/.timewarrior/extensions/` is executable and does **not** have the `.py` suffix.
* **Timezone Mismatch:** The script uses your system's local timezone to process UTC Timewarrior data. Verify your system clock is correct.

---

## Development & Debugging

### The "Tee" Hack

To see the raw data Timewarrior pipes into extensions, create a symlink to the `tee` command:

```bash
ln -s /usr/bin/tee ~/.timewarrior/extensions/Tee

```

Running `timew Tee :month` will dump the exact JSON and configuration headers to your terminal.

### Manual Testing

Capture a debug file to test logic changes without triggering Timewarrior:

```bash
timew Tee :month > debug.json
cat debug.json | python3 analysis.py --ignore Testing

```

---

## License

Distributed under the **MIT License**.

---
