"""Daily search automation for Microsoft Rewards."""
from playwright.sync_api import Page, Locator
import random
import config
from utils.human_behavior import random_delay_before_action


def _get_search_input_on_current_page(page: Page) -> Locator:
    """Find search input on the current page without navigating.

    Args:
        page: Playwright page instance

    Returns:
        Locator for the search input

    Raises:
        RuntimeError: If search input cannot be found
    """
    # Try multiple selectors commonly used by Bing
    selectors = [
        "input[name='q']",
        "#sb_form_q",
        "input[placeholder='Search']",
        "[aria-label='Search input']",
    ]

    for selector in selectors:
        search_input = page.locator(selector)
        if search_input.is_visible():
            return search_input

    raise RuntimeError("Search input not found on current page")


def _try_random_pagination(page: Page) -> bool:
    """Attempt to click a random pagination button during wait time.

    Args:
        page: Playwright page instance

    Returns:
        True if pagination was clicked, False otherwise
    """
    # Look for pagination elements
    pagination_selectors = [
        "a[aria-label='Page 2']",
        "a[aria-label='Page 3']",
        "a[aria-label='Page 4']",
        "a[aria-label='Page 5']",
        "li[class*='b_pag'] a",
        "#b_pagination a",
        ".pagination a",
    ]

    # Collect visible pagination links (page 2-5)
    visible_pages = []
    for selector in pagination_selectors:
        elements = page.locator(selector)
        count = elements.count()
        for i in range(count):
            el = elements.nth(i)
            if el.is_visible():
                text = el.text_content() or ""
                # Only click numeric page links (2-5)
                if text.strip().isdigit() and 2 <= int(text.strip()) <= 5:
                    visible_pages.append(el)

    if not visible_pages:
        return False

    # 40% chance to click a random page
    if random.random() < 0.4:
        page_num = random.randint(2, 5)
        for el in visible_pages:
            text = el.text_content() or ""
            if text.strip() == str(page_num):
                try:
                    el.click()
                    print(f"  [Pagination] Clicked page {page_num}")
                    page.wait_for_timeout(1500)
                    return True
                except Exception:
                    return False

    return False


def get_daily_search_points(page: Page) -> tuple[int, int]:
    """Check current daily search points from the rewards panel.

    Args:
        page: Playwright page instance

    Returns:
        Tuple of (earned_points, max_points) where points are Microsoft Rewards daily search points,
        or (-1, -1) if unable to retrieve.
    """
    import re
    try:
        # Click the points counter to open rewards panel
        points_container = page.locator(".b_clickarea[data-priority='2']")
        if not points_container.is_visible():
            print("[Points Check] Points container not visible")
            return (-1, -1)

        points_container.click()
        page.wait_for_timeout(3000)

        # Get the rewards panel iframe - title is 'Microsoft Rewards, expanded'
        fl = page.frame_locator("iframe[title='Microsoft Rewards, expanded']")

        # Wait for iframe content to load
        fl.locator("body").wait_for(timeout=10000)

        # Get all text in the iframe to parse search progress
        iframe_text = fl.locator("body").inner_text()

        # Method 1 (primary): Look for "每日搜索: X/Y" which is the actual daily search progress
        # e.g. "每日搜索\n54/60\n每天搜索并赚取最多 60 点积分"
        match = re.search(r'每日搜索\s*[:：]?\s*(\d+)\s*/\s*(\d+)', iframe_text)
        if match:
            earned = int(match.group(1))
            maximum = int(match.group(2))
            print(f"[Points Check] Daily search progress: {earned}/{maximum} (points via 每日搜索)")
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
            return (earned, maximum)

        # Method 2: Fallback - look for "你已获得 XX 积分" (points earned text)
        earned_match = re.search(r'你已获得\s*(\d+)\s*积分', iframe_text)
        max_match = re.search(r'最多\s*(\d+)\s*奖励积分', iframe_text)
        if earned_match and max_match:
            earned = int(earned_match.group(1))
            maximum = int(max_match.group(1))
            print(f"[Points Check] Daily search progress: {earned}/{maximum} (via earned+max text)")
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
            return (earned, maximum)

        # Method 3: "你已获得 XX 积分" alone (max unknown)
        if earned_match:
            earned = int(earned_match.group(1))
            print(f"[Points Check] Daily search earned: {earned}, max unknown")
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
            return (earned, -1)

        print(f"[Points Check] Could not find search progress in panel. Iframe text snippet:")
        print(iframe_text[:400])
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)
        return (-1, -1)

    except Exception as e:
        print(f"[Points Check] Error: {e}")
        try:
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
        except Exception:
            pass
        return (-1, -1)


# Default search terms for daily searches
DEFAULT_SEARCH_TERMS = [
    "人工智能",
    "机器学习",
    "云计算",
    "大数据",
    "物联网",
    "量子计算",
    "5G技术",
    "区块链",
    "自动驾驶",
    "新能源",
    "深度学习",
    "神经网络",
    "数据分析",
    "网络安全",
    "边缘计算",
    "虚拟现实",
    "增强现实",
    "智能家居",
    "智慧城市",
    "生物识别",
    "自然语言处理",
    "计算机视觉",
    "机器人技术",
    "3D打印",
    "无人机",
    "卫星导航",
    "基因编辑",
    "可穿戴设备",
    "智能医疗",
    "金融科技",
    "在线教育",
    "电子商务",
    "远程办公",
    "视频会议",
    "流媒体",
    "游戏引擎",
    "开源软件",
    "服务器架构",
    "容器技术",
    "微服务",
    "DevOps",
    "敏捷开发",
    "GitHub",
    "Stack Overflow",
    "Python编程",
    "JavaScript框架",
    "Web开发",
    "移动应用",
    "REST API",
    "GraphQL",
    "TypeScript",
    "React",
    "Vue.js",
    "Angular",
    "Node.js",
    "Django",
    "FastAPI",
    "Spring Boot",
    "Docker",
    "Kubernetes",
    "AWS云服务",
    "Azure云平台",
    "Google Cloud",
    "阿里云",
    "腾讯云",
    "华为云",
    "机器视觉",
    "图像识别",
    "语音助手",
    "智能音箱",
    "人脸识别",
    "指纹识别",
    "虹膜识别",
    "车牌识别",
    "医学影像",
    "疾病预测",
    "药物研发",
    "精准医疗",
    "远程监控",
    "智能农业",
    "精准灌溉",
    "无人机植保",
    "气象预报",
    "地震预警",
    "海洋监测",
    "森林防火",
    "城市交通",
    "智能电网",
    "储能技术",
    "氢能源",
    "太阳能",
    "风能发电",
    "核能技术",
    "碳中和",
    "碳交易",
    "环保技术",
    "污水处理",
    "垃圾分类",
    "循环利用",
    "可持续发展和绿色经济",
]


def perform_daily_searches(page: Page, count: int = None) -> int:
    """Perform daily random searches for Microsoft Rewards.

    Args:
        page: Playwright page instance
        count: Number of searches to perform (default from config.DAILY_SEARCH_GOAL)

    Returns:
        Number of searches completed successfully
    """
    if count is None:
        count = config.DAILY_SEARCH_GOAL

    completed = 0
    used_terms = set()

    print(f"Starting daily searches (goal: {count})...")

    # Navigate to Bing ONCE at the start
    page.goto(config.BING_URL)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)

    # Check current daily search points before starting
    earned, maximum = get_daily_search_points(page)
    if earned >= 0 and maximum > 0:
        print(f"[Pre-check] Daily search progress: {earned}/{maximum}")
        if earned >= maximum:
            print("[Pre-check] Daily search already at maximum! Skipping searches.")
            return 0

    # Get search terms (could be loaded from file in future)
    search_terms = DEFAULT_SEARCH_TERMS.copy()
    random.shuffle(search_terms)

    for i in range(count):
        # Check if daily search is already at maximum before each search
        earned, maximum = get_daily_search_points(page)
        if earned >= 0 and maximum > 0 and earned >= maximum:
            print(f"[Check] Daily search reached {earned}/{maximum}. Stopping search loop.")
            break

        # Select a unique search term
        available_terms = [t for t in search_terms if t not in used_terms]
        if not available_terms:
            # Reset if we run out of terms
            available_terms = DEFAULT_SEARCH_TERMS.copy()
            random.shuffle(available_terms)
            used_terms.clear()

        term = random.choice(available_terms)
        used_terms.add(term)

        print(f"Search {i + 1}/{count}: {term}")

        try:
            # Find search bar on CURRENT page (don't navigate away)
            search_input = _get_search_input_on_current_page(page)

            # Random delay before search
            random_delay_before_action()

            # Clear and type new search query using type() for proper Unicode support
            search_input.click()
            search_input.fill("")
            search_input.type(term, delay=random.randint(config.MIN_KEYSTROKE_DELAY_MS, config.MAX_KEYSTROKE_DELAY_MS))

            # Submit search
            page.keyboard.press("Enter")

            # Wait for search results
            page.wait_for_timeout(2000)

            # Try random pagination during wait time
            _try_random_pagination(page)

            # Verify search was executed
            if config.SEARCH_URL_PARAM in page.url or "search" in page.url.lower():
                completed += 1
                print(f"  -> Success!")
            else:
                print(f"  -> May have failed")

        except Exception as e:
            print(f"  -> Error: {e}")

        # Random wait between searches (3-8 seconds)
        page.wait_for_timeout(random.randint(3000, 8000))

    # Check daily search points after completing
    earned, maximum = get_daily_search_points(page)
    if earned >= 0 and maximum > 0:
        print(f"[Post-check] Daily search progress: {earned}/{maximum}")

    print(f"Daily searches completed: {completed}/{count}")
    return completed


def load_search_terms_from_file(filepath: str = None) -> list:
    """Load search terms from a file.

    Args:
        filepath: Path to search terms file (default: config.SEARCH_TERMS_FILE)

    Returns:
        List of search terms
    """
    if filepath is None:
        filepath = config.SEARCH_TERMS_FILE

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            terms = [line.strip() for line in f if line.strip()]
            if terms:
                return terms
    except FileNotFoundError:
        print(f"Search terms file not found: {filepath}")
    except Exception as e:
        print(f"Error loading search terms: {e}")

    return DEFAULT_SEARCH_TERMS


def get_random_search_terms(n: int = 10) -> list:
    """Get n random search terms.

    Args:
        n: Number of terms to return

    Returns:
        List of random search terms
    """
    terms = load_search_terms_from_file()
    return random.sample(terms, min(n, len(terms)))
