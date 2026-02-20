#!/usr/bin/env python3
"""
Timewarrior Hours Analysis Script
Includes toggleable weekly summaries with cumulative status.
"""

import json
import sys
import argparse
from datetime import datetime, timedelta, date, timezone
from collections import defaultdict
import re

# --- CONFIGURATION ---
# Tags in this list will be ignored by default. 
# You can add more at runtime using the --ignore flag.
DEFAULT_IGNORED_TAGS = ["SideQuest", "Lunch"]
# ---------------------

def parse_config_value(config_lines, key):
    """Search for a specific key in the Timewarrior config header"""
    for line in config_lines:
        if line.startswith(f"{key}:"):
            return line.split(":", 1)[1].strip().lower()
    return None

def parse_exclusions(config_lines):
    """Parse exclusion times to calculate projected hours per day"""
    exclusions = {}
    pattern = re.compile(r'exclusions\.(\w+):\s*<(\d+:\d+)\s*>(\d+:\d+)')
    
    for line in config_lines:
        match = pattern.match(line)
        if match:
            day = match.group(1).lower()
            start_parts = match.group(2).split(':')
            end_parts = match.group(3).split(':')
            start_minutes = int(start_parts[0]) * 60 + int(start_parts[1])
            end_minutes = int(end_parts[0]) * 60 + int(end_parts[1])
            exclusions[day] = (end_minutes - start_minutes) / 60.0
    return exclusions

def parse_holidays(config_lines):
    """Parse holiday dates"""
    holidays = set()
    pattern = re.compile(r'holidays\.US\.(\d{4}-\d{2}-\d{2}):\s*(.+)')
    for line in config_lines:
        match = pattern.match(line)
        if match:
            holidays.add(match.group(1))
    return holidays

def parse_time_entries(json_data, ignored_tags):
    """Parse time entries from JSON, filtering out ignored tags"""
    entries = []
    for entry in json_data:
        # If any of the entry's tags intersect with the ignored tags, skip this interval
        entry_tags = entry.get('tags', [])
        if ignored_tags and any(tag in ignored_tags for tag in entry_tags):
            continue
            
        start_dt = datetime.strptime(entry['start'], '%Y%m%dT%H%M%SZ')
        # Use timezone-aware UTC now, then strip tzinfo to match the naive datetime of start_dt
        end_dt = datetime.strptime(entry['end'], '%Y%m%dT%H%M%SZ') if 'end' in entry else datetime.now(timezone.utc).replace(tzinfo=None)
        
        duration = (end_dt - start_dt).total_seconds() / 3600.0
        entries.append({'start': start_dt, 'duration': duration})
    return entries

def get_local_offset():
    return datetime.now().astimezone().utcoffset()

def group_by_date(entries, local_offset):
    daily_totals = defaultdict(float)
    for entry in entries:
        local_date = (entry['start'] + local_offset).date()
        daily_totals[local_date] += entry['duration']
    return daily_totals

def get_date_range(daily_totals, holidays):
    if not daily_totals: return []
    min_date, max_date = min(daily_totals.keys()), max(daily_totals.keys())
    all_dates = set()
    curr = min_date
    while curr <= max_date:
        all_dates.add(curr)
        curr += timedelta(days=1)
    for h_str in holidays:
        try:
            h_date = datetime.strptime(h_str, '%Y-%m-%d').date()
            if min_date <= h_date <= max_date: all_dates.add(h_date)
        except ValueError: continue
    return sorted(all_dates)

def get_projected_hours(date_obj, exclusions, holidays, hours_per_day):
    date_str = date_obj.strftime('%Y-%m-%d')
    day_name = date_obj.strftime('%A').lower()
    
    if date_str in holidays:
        if day_name == 'friday':
            return 0.0
        return max(0.0, hours_per_day - 8.0)
    
    if day_name in ['saturday', 'sunday']:
        return 0.0
    
    return exclusions.get(day_name, 0.0)

def format_hours(hours, signed=False):
    sign = ""
    if signed:
        sign = "+" if hours >= 0 else "-"
    hours = abs(hours)
    h = int(hours)
    m = int((hours - h) * 60)
    return f"{sign}{h}:{m:02d}"

def print_week_summary(week_num, week_goal, week_actual, cum_goal, cum_actual, header_len):
    """
    Prints summary. 
    Columns show WEEKLY totals. 
    Text status shows CUMULATIVE (Running) totals.
    """
    diff = cum_actual - cum_goal
    status_text = "Ahead of" if diff >= 0 else "Behind"
    
    print("-" * header_len)
    print(f"Week {week_num:02d} Summary:   "
          f"{format_hours(week_goal):<10} "
          f"{format_hours(week_actual):<10} "
          f"({status_text} goal by {format_hours(diff)})")

def main():
    parser = argparse.ArgumentParser(description="Timewarrior Hours Analysis")
    parser.add_argument('--ignore', nargs='+', default=[], help="Additional tags to ignore (e.g., --ignore Clock Break)")
    
    # parse_known_args allows passing Timewarrior's standard piped input without crashing 
    args, _ = parser.parse_known_args()
    
    # Combine the hardcoded defaults with any runtime arguments provided
    ignored_tags = set(DEFAULT_IGNORED_TAGS + args.ignore)

    if sys.stdin.isatty():
        print("Usage: timew export | python3 script.py [--ignore TAG1 TAG2]", file=sys.stderr)
        sys.exit(1)
    
    input_data = sys.stdin.read().strip().split('\n')
    json_start = next((i for i, line in enumerate(input_data) if line.strip().startswith('[')), -1)
    if json_start == -1: sys.exit(1)
    
    config_lines = input_data[:json_start]
    json_text = '\n'.join(input_data[json_start:])
    
    exclusions = parse_exclusions(config_lines)
    holidays = parse_holidays(config_lines)
    
    # Custom configuration variables
    show_weekends = parse_config_value(config_lines, "projected.show_weekends") == "no"
    show_weekly_summary = parse_config_value(config_lines, "projected.weekly_summary") == "yes"
    
    hpd_str = parse_config_value(config_lines, "totals.hours_per_day")
    hours_per_day = float(hpd_str) if hpd_str else 8.0
    
    try:
        json_data = json.loads(json_text)
    except: sys.exit(1)
    
    daily_totals = group_by_date(parse_time_entries(json_data, ignored_tags), get_local_offset())
    all_dates = get_date_range(daily_totals, holidays)

    # Print the filtered tags in Timewarrior's rgb125 color (ANSI 69)
    if ignored_tags:
        color_rgb125 = "\033[38;5;69m"
        color_reset = "\033[0m"
        colored_tags = [f"{color_rgb125}{tag}{color_reset}" for tag in sorted(ignored_tags)]
        print(f"Excluded tags: {', '.join(colored_tags)}\n")
    
    header = f"{'Date':<18} {'Goal':<10} {'Worked':<10} {'Day +/-':<10} {'Total':<10} {'Status':<10}"
    print(header)
    print("-" * len(header))
    
    accum_actual = 0.0
    accum_proj = 0.0
    week_actual = 0.0
    week_proj = 0.0
    last_week = None
    
    for date_obj in all_dates:
        curr_week = date_obj.isocalendar()[1]
        
        # Check for week change
        if last_week is not None and curr_week != last_week:
            if show_weekly_summary:
                # Pass WEEK totals for columns, but ACCUM totals for status text
                print_week_summary(last_week, week_proj, week_actual, accum_proj, accum_actual, len(header))
                print("-" * len(header)) 
            else:
                print("-" * len(header))
            
            # Reset weekly counters
            week_actual = 0.0
            week_proj = 0.0
            
        last_week = curr_week

        actual = daily_totals.get(date_obj, 0.0)
        proj = get_projected_hours(date_obj, exclusions, holidays, hours_per_day)
        
        if show_weekends and date_obj.strftime('%A').lower() in ['saturday', 'sunday'] and actual == 0:
            continue

        accum_actual += actual
        accum_proj += proj
        week_actual += actual
        week_proj += proj
        
        day_diff = actual - proj
        total_diff = accum_actual - accum_proj
        indicator = "▲" if total_diff >= 0 else "▼"
        
        date_str = f"W{curr_week:02d} {date_obj.strftime('%b %a %d')}"
        
        print(f"{date_str:<18} "
              f"{format_hours(proj):<10} "
              f"{format_hours(actual):<10} "
              f"{format_hours(day_diff, True):<10} "
              f"{format_hours(accum_actual):<10} "
              f"{format_hours(total_diff, True)} {indicator}")

    # Final Weekly Summary for the last week in the report
    if show_weekly_summary and last_week is not None:
        print_week_summary(last_week, week_proj, week_actual, accum_proj, accum_actual, len(header))

if __name__ == '__main__':
    main()
