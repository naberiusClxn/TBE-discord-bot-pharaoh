import requests
from bs4 import BeautifulSoup

from main import API_KEY, STEAM_API_KEY

async def resolve_vanity_url(vanity_url: str) -> str:
    api_url = "https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/"
    params = {
        "key": STEAM_API_KEY,
        "vanityurl": vanity_url
    }

    try:
        response = requests.get(api_url, params=params, timeout=10)
        data = response.json()

        if data.get("response", {}).get("success") == 1:
            return data["response"]["steamid"]
        else:
            raise ValueError("Кастомный URL не найден или профиль приватный")

    except Exception as e:
        raise ValueError(f"Ошибка API Steam: {str(e)}")

def get_cs2_item_count(steam_id64: str):
    url = f"https://steamcommunity.com/profiles/{steam_id64}/inventory/"

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        cs2_tab = soup.find('a', id='inventory_link_730')
        if not cs2_tab:
            return 0

        count_span = cs2_tab.find('span', class_='games_list_tab_number')
        if not count_span:
            return 0

        return int(count_span.text.strip('()'))

    except Exception as e:
        return 0

def get_item_screenshot(inspect_link: str):
    url = "https://www.steamwebapi.com/steam/api/float/screenshot"
    params = {
        "inspect_link": inspect_link,
        "key": API_KEY
    }
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    return resp.json().get("image")


def get_inventory_value(steam_id: str):
    url = "https://www.steamwebapi.com/steam/api/inventory"
    params = {
        "steam_id": steam_id,
        "game": "cs2",
        "key": API_KEY,
        "parse": "true"
    }

    try:
        resp = requests.get(url, params=params)


        if resp.status_code == 403:
            raise requests.exceptions.HTTPError("Inventory is private", response=resp)

        resp.raise_for_status()
        items = resp.json()

        if not isinstance(items, list):
            raise ValueError("Invalid response from inventory API")

        total_value = 0.0
        tradable_count = 0
        cs2_items_count = len(items)
        top_items = sorted(items, key=lambda x: float(x.get("pricelatestsell") or 0), reverse=True)[:10]

        item_links = []
        item_names = []
        price_texts = []

        for item in items:
            price = item.get("pricelatestsell") or 0
            total_value += price

            if item.get("marketable", False):
                tradable_count += 1

            name = item.get("markethashname") or item.get("marketname") or "Без названия"
            price_text = f"${price:.2f}" if price else "0.00"
            item_names.append(name)
            price_texts.append(price_text)

        top_items_info = [
            {
                "name": item.get("markethashname") or item.get("marketname") or "Без названия",
                "price": f"${float(item.get('pricelatestsell') or 0):.2f}",
                "image": item.get("image")
            }
            for item in top_items
        ]

        screenshot = None

        return (total_value, cs2_items_count, tradable_count, top_items_info,
                item_links, item_names, price_texts, screenshot)

    except requests.exceptions.RequestException as e:
        raise e
    except Exception as e:
        raise ValueError(f"Error while processing inventory: {str(e)}")