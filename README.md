Here is the updated README with the new tag filtering feature seamlessly integrated into the Features, Configuration, and Usage sections.

```markdown
# Timewarrior Hours Analysis (`projected`)

A Python-based extension for [Timewarrior](https://timewarrior.net/) that provides a detailed daily breakdown of work hours, holiday handling, and "accumulated vs. projected" totals to help you stay on track with your monthly goals.

---

## Features

* **Daily Breakdown:** See exactly how many hours you worked each day.
* **Monthly Projections:** Tracks your progress against a monthly target based on your custom schedule.
* **Holiday Aware:** Automatically adjusts projections for holidays based on your standard work day length.
* **Tag Filtering:** Automatically exclude intervals containing specific tags (e.g., breaks or personal tasks) from your total hours worked. Set defaults in the script or pass them at runtime.
* **Weekend Filtering:** Option to hide weekends if no time was recorded.
* **Timezone Aware:** Automatically converts UTC Timewarrior data to your local timezone.
* **Human-Readable Output:** Features week-by-week dividers and status indicators (▲/▼).

---

## Example Output

```text
Date               Goal       Worked     Day +/-    Total      Status
-----------------------------------------------------------------------
W01 Jan Mon 02     9:00       8:30       -0:30      8:30       -0:30 ▼
W01 Jan Tue 03     9:00       9:45       +0:45      18:15      +0:15 ▲
W01 Jan Wed 04     1:00       0:00       -1:00      18:15      -0:45 ▼  ← Holiday
W01 Jan Thu 05     9:00       9:10       +0:10      27:25      -0:35 ▼
-----------------------------------------------------------------------
Week 01 Summary:   28:00      27:25      (Behind goal by 0:35)


```

> [!IMPORTANT]
> **Holiday Note:** One (1) extra hour is added to the goal on holidays because the company pays 8 hours for the holiday, but the 9/80 schedule requires 9 hours for the day to be "covered."

---

## Installation

### 1. Link the Extension

Timewarrior looks for executable scripts in its extensions directory. Create a symbolic link from your repository to the Timewarrior extensions folder:

```bash
ln -s /path/to/your/repo/analysis.py ~/.timewarrior/extensions/projected
chmod +x ~/.timewarrior/extensions/projected

```

> **Note:** The name of the link (`projected`) becomes the command you type in Timewarrior.

### 2. Configure Timewarrior

The script relies on your settings to determine your daily "Target" hours. Add your schedule, holiday preferences, and report behavior to your `~/.timewarrior/timewarrior.cfg`:

```ini
# Define your work hours (Exclusions are when you ARE NOT working)
# The script calculates the gaps to determine your daily target.
exclusions.monday:    <00:00 >09:00 <17:00 >24:00
exclusions.tuesday:   <00:00 >09:00 <17:00 >24:00
exclusions.wednesday: <00:00 >09:00 <17:00 >24:00
exclusions.thursday:  <00:00 >09:00 <17:00 >24:00
exclusions.friday:    <00:00 >09:00 <17:00 >24:00

# Set your standard work day length (defaults to 8 if not set)
# Holidays are credited for 8 hours; if your day is longer, 
# the difference is added as a goal for the holiday.
totals.hours_per_day = 9

# Hide weekends with no recorded time by default
projected.show_weekends = no

# Enable a summary line at the end of every week
projected.weekly_summary = yes

# Define Holidays
holidays.US.2026-01-01: New Year's Day
holidays.US.2026-12-25: Christmas


```

### 3. Set Default Ignored Tags

Open the `projected` script and modify the `DEFAULT_IGNORED_TAGS` list near the top of the file to include tags you always want excluded from your totals:

```python
# --- CONFIGURATION ---
# Tags in this list will be ignored by default. 
# You can add more at runtime using the --ignore flag.
DEFAULT_IGNORED_TAGS = ["SideQuest", "Nap"]
# ---------------------

```

### 4. Create Shell Aliases

To make the report easily accessible, add these aliases to your `~/.bash_aliases` or `~/.zshrc` file:

```bash
# Current month report
alias twp='timew projected :month'

# Last month report
alias twlp='timew projected :lastmonth'

# Filtered by tag
alias twpt='timew projected :month tag_name'


```

---

## Usage

### Basic Commands

Once the aliases are set, you can simply run:

* `twp`: Show the report for the current month.
* `twlp`: Show the report for the previous month.

### Dynamic Arguments & Tag Filtering

You can override your default configuration or add custom filters on-the-fly when running the command.

**Ignoring specific tags:**
Pass the `--ignore` flag to exclude specific tags from the total hours calculation for a single run. This combines with your `DEFAULT_IGNORED_TAGS`.

```bash
# Ignore intervals tagged with "Clock" or "Break"
timew projected :month --ignore Clock Break

```

**Overriding RC Configs:**
You can override `timewarrior.cfg` settings using `rc` flags.

```bash
# Force weekends to show for this specific run
timew projected :month rc.projected.show_weekends=yes

# Force weekly_summary to show for this specific run
timew projected :month rc.projected.weekly_summary=yes

```

---

## Report Preview

The output is designed to be easily scannable:

* **Goal:** Your target hours for that day (adjusted for holidays and exclusions).
* **Worked:** Actual time recorded in Timewarrior.
* **Day +/-:** Performance for that specific day relative to the goal.
* **Status:** Running total difference for the month (▲ ahead / ▼ behind).

---

## Technical Details: How it Works

This script acts as a Timewarrior **extension**. When you run `timew projected`, Timewarrior:

1. Exports the relevant time intervals as JSON.
2. Prepends the current configuration settings as a header.
3. Pipes all of this into the script's `stdin`.

The script parses the configuration header to find your `exclusions`, `totals.hours_per_day`, and the `projected.show_weekends` flag before processing the JSON interval data. It also leverages `argparse` to safely intercept the `--ignore` flag from standard Timewarrior input streams.

---

## License

Distributed under the **MIT License** – see `LICENSE` for details.

---

## Contributing

* Fork the repository, make your changes, and open a Pull Request.
* Bug reports, feature ideas (e.g., per‑country holiday calendars), and documentation improvements are most welcome.

---

```

Would you like me to help write a quick bash script to automatically deploy these code and README updates to your repository and symlink them, or are you good to copy this over manually?

```