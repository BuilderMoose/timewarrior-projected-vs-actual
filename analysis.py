#!/usr/bin/env python3
"""
Timewarrior Hours Analysis Script
Includes toggleable weekly summaries with cumulative status and tag exclusions.
"""

import json
import sys
import argparse
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import re

# --- CONFIGURATION ---
DEFAULT_IGNORED_TAGS = []
COLOR_RGB125 = "\033[38;5;69m"
COLOR_RESET = "\033[0m"

# --- HELPER FUNCTIONS ---

def parse_config_value(config_lines, key):
    """Search for a specific key in the Timewarrior config header."""
    for line in config_lines:
        if line.startswith(f"{key}:"):
            return line.split(":", 1)[1].strip()
    return None

def parse_exclusions(config_lines):
    """Parse exclusion times to calculate projected hours per day."""
    exclusions = {}
    pattern = re.compile(r'exclusions\.(\w+):\s*<(\d+:\d+)\s*>(\d+:\d+)')
    for line in config_lines:
        match = pattern.match(line)
        if match:
            day = match.group(1).lower()
            start_parts = match.group(2).split(':')
            end_parts = match.group(3).split(':')
            start_m = int(start_parts[0]) * 60 + int(start_parts[1])
            end_m = int(end_parts[0]) * 60 + int(end_parts[1])
            exclusions[day] = (end_m - start_m) / 60.0
    return exclusions

def parse_holidays(config_lines):
    """Parse holiday dates from the config."""
    holidays = set()
    pattern = re.compile(r'holidays\.US\.(\d{4}-\d{2}-\d{2}):\s*(.+)')
    for line in config_lines:
        match = pattern.match(line)
        if match:
            holidays.add(match.group(1))
    return holidays

def parse_time_entries(json_data, ignored_tags):
    """
    Parses entries, separating worked time from excluded tag time.
    """
    entries = []
    excluded_summary = defaultdict(float)
    
    for entry in json_data:
        start_dt = datetime.strptime(entry['start'], '%Y%m%dT%H%M%SZ')
        # Handle open intervals
        if 'end' in entry:
            end_dt = datetime.strptime(entry['end'], '%Y%m%dT%H%M%SZ')
        else:
            end_dt = datetime.utcnow()
            
        duration = (end_dt - start_dt).total_seconds() / 3600.0
        entry_tags = entry.get('tags', [])

        # If entry has an ignored tag, add to summary and skip main total
        intersecting = [t for t in entry_tags if t in ignored_tags]
        if intersecting:
            for tag in intersecting:
                excluded_summary[tag] += duration
            continue
            
        entries.append({'start': start_dt, 'duration': duration})
    return entries, excluded_summary

def get_projected_hours(date_obj, exclusions, holidays, hours_per_day):
    """Calculates the expected work hours for a specific date."""
    date_str = date_obj.strftime('%Y-%m-%d')
    day_name = date_obj.strftime('%A').lower()

    if date_str in holidays:
        return 0.0 if day_name == 'friday' else max(0.0, hours_per_day - 8.0)

    if day_name in ['saturday', 'sunday']:
        return 0.0

    return exclusions.get(day_name, 0.0)

def format_hours(hours, signed=False):
    """Formats float hours to H:MM string."""
    sign = ""
    if signed:
        sign = "+" if hours >= 0 else "-"
    hours = abs(hours)
    h, m = int(hours), int((hours - int(hours)) * 60)
    return f"{sign}{h}:{m:02d}"

def print_week_summary(week_num, week_goal, week_actual, cum_goal, cum_actual, header_len):
    """Prints the weekly total row and cumulative status."""
    diff = cum_actual - cum_goal
    status_text = "Ahead of" if diff >= 0 else "Behind"
    
    print("-" * header_len)
    print(f"Week {week_num:02d} Summary:   "
          f"{format_hours(week_goal):<10} "
          f"{format_hours(week_actual):<10} "
          f"({status_text} goal by {format_hours(diff)})")

# --- MAIN ---

def main():
    parser = argparse.ArgumentParser(description="Timewarrior Hours Analysis")
    parser.add_argument('--ignore', nargs='+', default=[], help="Additional tags to ignore")
    args, _ = parser.parse_known_args()

    if sys.stdin.isatty():
        print("Usage: timew export | python3 script.py [--ignore TAG]", file=sys.stderr)
        sys.exit(1)
    
    input_data = sys.stdin.read().strip().split('\n')
    json_start = next((i for i, line in enumerate(input_data) if line.strip().startswith('[')), -1)
    if json_start == -1: sys.exit(1)
    
    config_lines = input_data[:json_start]
    json_text = '\n'.join(input_data[json_start:])
    
    # 1. Config Parsing
    config_tags_raw = parse_config_value(config_lines, "projected.ignore_tags")
    config_tags = config_tags_raw.split() if config_tags_raw else []
    ignored_tags = set(DEFAULT_IGNORED_TAGS + config_tags + args.ignore)
    
    exclusions = parse_exclusions(config_lines)
    holidays = parse_holidays(config_lines)
    
    hide_weekends = parse_config_value(config_lines, "projected.show_weekends") == "no"
    show_weekly_summary = parse_config_value(config_lines, "projected.weekly_summary") == "yes"
    summarize_excluded = parse_config_value(config_lines, "projected.summarize_excluded") == "yes"
    
    hpd_str = parse_config_value(config_lines, "totals.hours_per_day")
    hours_per_day = float(hpd_str) if hpd_str else 8.0
    
    # 2. Data Processing
    try:
        json_data = json.loads(json_text)
    except:
        sys.exit(1)
    
    entries, excluded_summary = parse_time_entries(json_data, ignored_tags)
    
    # Group by local date
    daily_totals = defaultdict(float)
    local_offset = datetime.now().astimezone().utcoffset()
    for entry in entries:
        local_date = (entry['start'] + local_offset).date()
        daily_totals[local_date] += entry['duration']
    
    if not daily_totals:
        return

    # Create continuous date range
    min_date, max_date = min(daily_totals.keys()), max(daily_totals.keys())
    all_dates = []
    curr = min_date
    while curr <= max_date:
        all_dates.append(curr)
        curr += timedelta(days=1)
    all_dates.sort()

    # 3. Output
    if ignored_tags:
        colored_tags = [f"{COLOR_RGB125}{tag}{COLOR_RESET}" for tag in sorted(ignored_tags)]
        print(f"Excluded tags: {', '.join(colored_tags)}\n")
    
    header = f"{'Date':<18} {'Goal':<10} {'Worked':<10} {'Day +/-':<10} {'Total':<10} {'Status':<10}"
    print(header)
    print("-" * len(header))
    
    accum_actual, accum_proj = 0.0, 0.0
    week_actual, week_proj = 0.0, 0.0
    last_week = None
    
    for date_obj in all_dates:
        curr_week = date_obj.isocalendar()[1]
        
        if last_week is not None and curr_week != last_week:
            if show_weekly_summary:
                print_week_summary(last_week, week_proj, week_actual, accum_proj, accum_actual, len(header))
            print("-" * len(header))
            week_actual, week_proj = 0.0, 0.0
        
        last_week = curr_week
        actual = daily_totals.get(date_obj, 0.0)
        proj = get_projected_hours(date_obj, exclusions, holidays, hours_per_day)

        if hide_weekends and date_obj.strftime('%A').lower() in ['saturday', 'sunday'] and actual == 0:
            continue

        accum_actual += actual
        accum_proj += proj
        week_actual += actual
        week_proj += proj
        
        day_diff, total_diff = actual - proj, accum_actual - accum_proj
        indicator = "▲" if total_diff >= 0 else "▼"
        date_label = f"W{curr_week:02d} {date_obj.strftime('%b %a %d')}"
        
        print(f"{date_label:<18} "
              f"{format_hours(proj):<10} "
              f"{format_hours(actual):<10} "
              f"{format_hours(day_diff, True):<10} "
              f"{format_hours(accum_actual):<10} "
              f"{format_hours(total_diff, True)} {indicator}")

    if show_weekly_summary and last_week is not None:
        print_week_summary(last_week, week_proj, week_actual, accum_proj, accum_actual, len(header))

    if summarize_excluded and excluded_summary:
        print("\nExcluded Time Summary:")
        print("-" * 30)
        for tag in sorted(excluded_summary.keys()):
            col_tag = f"{COLOR_RGB125}{tag}{COLOR_RESET}"
            print(f"{col_tag:<27} {format_hours(excluded_summary[tag])}")

if __name__ == '__main__':
    main()
