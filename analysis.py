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
#DEFAULT_IGNORED_TAGS = ["SideQuest", "Lunch"]
DEFAULT_IGNORED_TAGS = []
COLOR_RGB125 = "\033[38;5;69m"
COLOR_RESET = "\033[0m"
# ---------------------

def parse_config_value(config_lines, key):
    """Search for a specific key in the Timewarrior config header"""
    for line in config_lines:
        if line.startswith(f"{key}:"):
            return line.split(":", 1)[1].strip()
    return None

def parse_exclusions(config_lines):
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
    holidays = set()
    pattern = re.compile(r'holidays\.US\.(\d{4}-\d{2}-\d{2}):\s*(.+)')
    for line in config_lines:
        match = pattern.match(line)
        if match:
            holidays.add(match.group(1))
    return holidays

def parse_time_entries(json_data, ignored_tags):
    entries = []
    excluded_summary = defaultdict(float)
    for entry in json_data:
        entry_tags = entry.get('tags', [])
        start_dt = datetime.strptime(entry['start'], '%Y%m%dT%H%M%SZ')
        end_dt = datetime.strptime(entry['end'], '%Y%m%dT%H%M%SZ') if 'end' in entry \
                 else datetime.now(timezone.utc).replace(tzinfo=None)
        duration = (end_dt - start_dt).total_seconds() / 3600.0

        intersecting_tags = [tag for tag in entry_tags if tag in ignored_tags]
        if intersecting_tags:
            for tag in intersecting_tags:
                excluded_summary[tag] += duration
            continue
        entries.append({'start': start_dt, 'duration': duration})
    return entries, excluded_summary

def get_local_offset():
    return datetime.now().astimezone().utcoffset()

def format_hours(hours, signed=False):
    sign = ""
    if signed: sign = "+" if hours >= 0 else "-"
    hours = abs(hours)
    h, m = int(hours), int((hours - int(hours)) * 60)
    return f"{sign}{h}:{m:02d}"

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
    
    # --- CONFIG PARSING ---
    # Parse ignored tags from config: projected.ignore_tags = Tag1 Tag2
    config_tags_raw = parse_config_value(config_lines, "projected.ignore_tags")
    config_tags = config_tags_raw.split() if config_tags_raw else []
    
    # Combine all sources
    ignored_tags = set(DEFAULT_IGNORED_TAGS + config_tags + args.ignore)
    
    exclusions = parse_exclusions(config_lines)
    holidays = parse_holidays(config_lines)
    show_weekends = parse_config_value(config_lines, "projected.show_weekends") == "no"
    show_weekly_summary = parse_config_value(config_lines, "projected.weekly_summary") == "yes"
    summarize_excluded = parse_config_value(config_lines, "projected.summarize_excluded") == "yes"
    hpd_str = parse_config_value(config_lines, "totals.hours_per_day")
    hours_per_day = float(hpd_str) if hpd_str else 8.0
    
    try:
        json_data = json.loads(json_text)
    except: sys.exit(1)
    
    # --- DATA PROCESSING ---
    entries, excluded_summary = parse_time_entries(json_data, ignored_tags)
    daily_totals = defaultdict(float)
    local_offset = get_local_offset()
    for entry in entries:
        local_date = (entry['start'] + local_offset).date()
        daily_totals[local_date] += entry['duration']
    
    if not daily_totals: return
    min_date, max_date = min(daily_totals.keys()), max(daily_totals.keys())
    all_dates = []
    curr = min_date
    while curr <= max_date:
        all_dates.append(curr)
        curr += timedelta(days=1)

    # --- OUTPUT ---
    if ignored_tags:
        colored_tags = [f"{COLOR_RGB125}{tag}{COLOR_RESET}" for tag in sorted(ignored_tags)]
        print(f"Excluded tags: {', '.join(colored_tags)}\n")
    
    header = f"{'Date':<18} {'Goal':<10} {'Worked':<10} {'Day +/-':<10} {'Total':<10} {'Status':<10}"
    print(header)
    print("-" * len(header))
    
    accum_actual, accum_proj = 0.0, 0.0
    week_actual, week_proj = 0.0, 0.0
    last_week = None
    
    for date_obj in sorted(all_dates):
        curr_week = date_obj.isocalendar()[1]
        if last_week is not None and curr_week != last_week:
            if show_weekly_summary:
                diff = accum_actual - accum_proj
                print("-" * len(header))
                print(f"Week {last_week:02d} Summary:   "
                      f"{format_hours(week_proj):<10} {format_hours(week_actual):<10} "
                      f"({'Ahead of' if diff >= 0 else 'Behind'} goal by {format_hours(diff)})")
                print("-" * len(header)) 
            else:
                print("-" * len(header))
            week_actual, week_proj = 0.0, 0.0
        last_week = curr_week

        actual = daily_totals.get(date_obj, 0.0)
        
        # Projected Math
        date_str, day_name = date_obj.strftime('%Y-%m-%d'), date_obj.strftime('%A').lower()
        if date_str in holidays:
            proj = 0.0 if day_name == 'friday' else max(0.0, hours_per_day - 8.0)
        elif day_name in ['saturday', 'sunday']:
            proj = 0.0
        else:
            proj = exclusions.get(day_name, 0.0)

        if show_weekends and day_name in ['saturday', 'sunday'] and actual == 0: continue

        accum_actual += actual
        accum_proj += proj
        week_actual += actual
        week_proj += proj
        
        day_diff, total_diff = actual - proj, accum_actual - accum_proj
        print(f"W{curr_week:02d} {date_obj.strftime('%b %a %d'):<13} "
              f"{format_hours(proj):<10} {format_hours(actual):<10} "
              f"{format_hours(day_diff, True):<10} {format_hours(accum_actual):<10} "
              f"{format_hours(total_diff, True)} {'▲' if total_diff >= 0 else '▼'}")

    # Final summary footer
    if summarize_excluded and excluded_summary:
        print("\nExcluded Time Summary:")
        print("-" * 30)
        for tag in sorted(excluded_summary.keys()):
            colored_tag = f"{COLOR_RGB125}{tag}{COLOR_RESET}"
            print(f"{colored_tag:<27} {format_hours(excluded_summary[tag])}")

if __name__ == '__main__':
    main()
