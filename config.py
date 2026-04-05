"""Configuration for Edge Browser Search Automation."""
import os
import json

# Browser settings
HEADLESS = False
VIEWPORT = {"width": 1920, "height": 1080}

# Load profile configuration from JSON
PROFILE_CONFIG_FILE = "profiles.json"


def _load_profile_config() -> dict:
    """Load profile configuration from JSON file.

    Returns:
        Dictionary with profile configuration
    """
    config_path = os.path.join(os.path.dirname(__file__), PROFILE_CONFIG_FILE)
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[Config] Failed to load {PROFILE_CONFIG_FILE}: {e}")
        return {}


_profile_config = _load_profile_config()

# Edge profile settings from JSON
PROFILES = _profile_config.get('profiles', [])
PROFILE_BASE = os.path.expanduser(_profile_config.get('profile_base', '~/.config/microsoft-edge'))
AUTO_DETECT_PROFILES = _profile_config.get('auto_detect_profiles', False)


def _scan_available_profiles() -> list:
    """Scan Edge profile directory to find available profiles.

    Returns:
        List of profile names found
    """
    if not os.path.exists(PROFILE_BASE):
        return []

    profiles = []
    for name in os.listdir(PROFILE_BASE):
        profile_path = os.path.join(PROFILE_BASE, name)
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
        print("[Config] No profiles auto-detected, falling back to profiles.json")
    return PROFILES


def get_profile_path_from_config(index: int = 0) -> str:
    """Get profile path by index.

    Args:
        index: Profile index in profiles list

    Returns:
        Full path to the profile directory
    """
    profiles = get_all_profile_paths()
    if index < len(profiles):
        return os.path.join(PROFILE_BASE, profiles[index])
    return os.path.join(PROFILE_BASE, profiles[0])


def add_profile_to_config(profile_name: str) -> bool:
    """Add a new profile to profiles.json.

    Args:
        profile_name: Name of the profile to add

    Returns:
        True if added successfully, False otherwise
    """
    config_path = os.path.join(os.path.dirname(__file__), PROFILE_CONFIG_FILE)
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)

        profiles = config_data.get('profiles', [])
        if profile_name in profiles:
            print(f"[Config] Profile '{profile_name}' already exists in profiles.json")
            return False

        profiles.append(profile_name)
        config_data['profiles'] = profiles

        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)

        # Update module-level variable
        global PROFILES
        PROFILES = profiles

        print(f"[Config] Added profile '{profile_name}' to profiles.json")
        return True
    except Exception as e:
        print(f"[Config] Failed to add profile: {e}")
        return False

# Bing settings
BING_URL = "https://cn.bing.com"

# Random text API
RANDOM_TEXT_API_URL = "https://site.gxyunyun.com/tools-v1/random-text"


def fetch_random_text() -> str:
    """Fetch random text from API.

    Returns:
        Random text string, or empty string on failure
    """
    import urllib.request
    import urllib.error

    try:
        req = urllib.request.Request(RANDOM_TEXT_API_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                if data and data.get('text'):
                    return data['text']
    except Exception as e:
        print(f"[Config] Failed to fetch random text: {e}")
    return ""

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
