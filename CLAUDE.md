# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Microsoft Rewards automation agent that automates Bing searches and rewards activities using Playwright-driven Microsoft Edge browser automation. Supports multiple Edge profiles (accounts) with anti-detection measures.

## Running the Agent

```bash
# Default run (all accounts, full automation)
python main.py

# Login mode (opens browser for manual login, saves state)
python main.py --login

# Login mode with new profile (auto-added to profiles.json)
python main.py --login -p="Profile 3"

# Search only mode
python main.py --search-only

# Activities only mode (quizzes, polls, smart searches)
python main.py --activities-only

# Custom search count
python main.py --searches=50
```

## Architecture

### Module Structure

- **`main.py`** - Entry point with TUI profile selector (arrow keys + space + enter), orchestrates automation per profile
- **`config.py`** - Configuration: browser settings, delays, Bing URL, search goals; profiles loaded from `profiles.json`
- **`profiles.json`** - Profile configuration: list of Edge profile names and base path
- **`browser/edge_launcher.py`** - Launches Edge/Chromium with anti-detection args (`--disable-blink-features=AutomationControlled`)
- **`search/`** - Bing navigation and search input:
  - `bing_navigator.py` - Navigate to Bing, verify search box visible
  - `search_input.py` - Type queries with human-like keystroke delays
- **`state/session_manager.py`** - Browser session persistence via `storage_state`
- **`utils/`** - Anti-detection helpers:
  - `human_behavior.py` - Random delays before actions (9-40s between operations)
  - `retry.py` - Decorator for retrying failed operations
- **`rewards/`** - Microsoft Rewards automation:
  - `daily_search.py` - Performs random Bing searches, checks daily search progress via rewards panel iframe
  - `activity_discovery.py` - Discovers available activities on rewards dashboard
  - `activity_executor.py` - Executes quizzes, polls, smart searches; handles activity cards via multiple selector fallbacks

### Key Design Patterns

- **Selector fallback chains** - All activity/poll/quiz execution tries multiple CSS selectors and XPath patterns
- **Anti-detection** - Random delays (9-40s between actions, 200-600ms keystroke delays), removes automation flags
- **Multi-profile** - Each Edge profile = different Microsoft account; profiles configured in `profiles.json`
- **State persistence** - Login state saved to `edge_search_state.json` to avoid re-logging

### Rewards Points Flow

1. Navigate to Bing (`config.BING_URL` = `https://cn.bing.com`)
2. Check daily search progress via rewards panel iframe
3. If not maxed, perform `DAILY_SEARCH_GOAL` (30) random searches using Chinese tech terms
4. Navigate to `https://rewards.bing.com` to execute activities
5. Activity types: quizzes, polls, smart_searches, other (click-based activities)
