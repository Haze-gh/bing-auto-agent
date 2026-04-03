"""Configuration for Edge Browser Search Automation."""
import os

# Browser settings
HEADLESS = False
VIEWPORT = {"width": 1920, "height": 1080}

# Edge profile settings
# Option 1: Specify full path directly
# Option 2: Specify profile name + base path (more portable)
# Multiple profiles supported - each profile is a different account
EDGE_PROFILE_NAMES = ['Default', 'Profile 1', 'Profile 2']  # e.g., ['Default', 'Profile 1', 'Profile 2']
EDGE_PROFILE_BASE = os.path.expanduser('~/.config/microsoft-edge')

# Auto-detect profiles
AUTO_DETECT_PROFILES = False  # Set to True to auto-scan profiles


def _scan_available_profiles() -> list:
    """Scan Edge profile directory to find available profiles.

    Returns:
        List of profile names found
    """
    import os
    if not os.path.exists(EDGE_PROFILE_BASE):
        return []

    profiles = []
    for name in os.listdir(EDGE_PROFILE_BASE):
        profile_path = os.path.join(EDGE_PROFILE_BASE, name)
        # Check if it's a directory (profile folder)
        if not os.path.isdir(profile_path):
            continue
        # Skip certain system folders
        if name in ['System Profile', 'Crashpad', 'component_crx_cache',
                     'extensions_crx_cache', 'ShaderCache', 'GrShaderCache',
                     'MEIPreload', 'Local Traces', 'hyphen-data']:
            continue
        # Real profiles have a Preferences file or Sessions etc.
        if os.path.exists(os.path.join(profile_path, 'Preferences')) or \
           os.path.exists(os.path.join(profile_path, 'Sessions')) or \
           name.startswith('Profile'):
            profiles.append(name)

    return sorted(profiles)


def get_all_profile_paths() -> list:
    """Get list of all profile paths based on auto-detection or manual config.

    Returns:
        List of profile names
    """
    if AUTO_DETECT_PROFILES:
        detected = _scan_available_profiles()
        if detected:
            print(f"[Config] Auto-detected {len(detected)} profiles: {detected}")
            return detected
        print("[Config] No profiles auto-detected, falling back to EDGE_PROFILE_NAMES")
    return EDGE_PROFILE_NAMES


def get_profile_path_from_config(index: int = 0) -> str:
    """Get profile path by index.

    Args:
        index: Profile index in EDGE_PROFILE_NAMES list

    Returns:
        Full path to the profile directory
    """
    profiles = get_all_profile_paths()
    if index < len(profiles):
        return os.path.join(EDGE_PROFILE_BASE, profiles[index])
    return os.path.join(EDGE_PROFILE_BASE, profiles[0])

# Bing settings
BING_URL = "https://cn.bing.com"

# Anti-detection settings
MIN_DELAY_MS = 9000
MAX_DELAY_MS = 40000
MIN_KEYSTROKE_DELAY_MS = 200
MAX_KEYSTROKE_DELAY_MS = 600

# Retry settings
RETRY_TIMEOUT = 30
RETRY_INTERVAL = 2

# State file
STATE_FILE = "edge_search_state.json"

# Search verification
SEARCH_URL_PARAM = "q="

# Rewards settings
DAILY_SEARCH_GOAL = 30
SEARCH_TERMS_FILE = "search_terms.txt"

# Activity settings
ACTIVITY_DELAY_MIN = 3000
ACTIVITY_DELAY_MAX = 8000
