# Timewarrior Hours Analysis (`projected`)

A Python-based extension for [Timewarrior](https://timewarrior.net/) that provides a detailed daily breakdown of work hours, holiday handling, and "accumulated vs. projected" totals to help you stay on track with your monthly goals.

---

## Features

* **Daily Breakdown:** See exactly how many hours you worked each day.
* **Monthly Projections:** Tracks your progress against a monthly target based on your custom schedule.
* **Holiday Aware:** Automatically adjusts projections for holidays (configurable).
* **Weekend Filtering:** Option to hide weekends if no time was recorded.
* **Timezone Aware:** Automatically converts UTC Timewarrior data to your local timezone.
* **Human-Readable Output:** Features week-by-week dividers and status indicators (▲/▼).

---

## Installation

### 1. Link the Extension
Timewarrior looks for executable scripts in its extensions directory. Create a symbolic link from your repository to the Timewarrior extensions folder:

```bash
ln -s /path/to/your/repo/analysis.py ~/.timewarrior/extensions/projected
chmod +x ~/.timewarrior/extensions/projected



> **Note:** The name of the link (`projected`) becomes the command you type in Timewarrior.

### 2. Configure Timewarrior

The script relies on your `exclusions` settings to determine your daily "Target" hours. Add your work schedule and holiday preferences to your `~/.timewarrior/timewarrior.cfg`:

```ini
# Define your work hours (Exclusions are when you ARE NOT working)
# The script calculates the gaps to determine your daily target.
exclusions.monday:    <00:00 >09:00 <17:00 >24:00
exclusions.tuesday:   <00:00 >09:00 <17:00 >24:00
exclusions.wednesday: <00:00 >09:00 <17:00 >24:00
exclusions.thursday:  <00:00 >09:00 <17:00 >24:00
exclusions.friday:    <00:00 >09:00 <17:00 >24:00

# Optional: Hide weekends with no recorded time by default
projected.noweekend = yes

# Define Holidays (Script counts these as 1hr targets Mon-Thu, 0hr Fri)
holidays.US.2026-01-01: New Year's Day
holidays.US.2026-12-25: Christmas

```

### 3. Create Shell Aliases

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

### Dynamic Arguments (RC Overrides)

You can override your default configuration on-the-fly using `rc` flags. This is useful if you want to see weekends even if `projected.noweekend` is set to `yes`.

```bash
# Force weekends to show for this specific run
timew projected :month rc.projected.noweekend=no

```

---

## Report Preview

The output is designed to be easily scannable:

* **Goal:** Your target hours for that day.
* **Worked:** Actual time recorded.
* **Day +/-:** Performance for that specific day.
* **Status:** Running total difference for the month (▲ ahead / ▼ behind).

---

## Technical Details: How it Works

This script acts as a Timewarrior **extension**. When you run `timew projected`, Timewarrior:

1. Exports the relevant time intervals as JSON.
2. Prepends the current configuration settings as a header.
3. Pipes all of this into the script's `stdin`.

The script parses the configuration header to find your `exclusions` (to set targets) and the custom `projected.noweekend` flag before processing the JSON interval data.
