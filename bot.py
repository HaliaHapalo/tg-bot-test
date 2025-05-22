import requests
import re
import time
from bs4 import BeautifulSoup

# 📌 Конфігурація
token = "1805866272:AAEVjVuESub14bCqG_BgkgLjWD1lscLdn6A"
chat_id = "-1001498779171"
novelty_page_url = "https://pp-books.com.ua/novynka/?orderby=date&paged=1"

# 🔖 HTTP-заголовок браузера
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    )
}

# 🌐 Завантажити HTML сторінки
def get_html(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"[❌] Помилка завантаження сторінки {url}: {e}")
        return None

# 📥 Отримати новинки (посилання + зображення)
def get_latest_items():
    html = get_html(novelty_page_url)
    if not html:
        return [], []

    soup = BeautifulSoup(html, "html.parser")
    items = soup.select("div.product-element-top.wd-quick-shop")

    links = []
    images = []

    for item in items:
        a_tag = item.find("a", href=True)
        img_tag = item.find("img")

        if a_tag and a_tag["href"]:
            links.append(a_tag["href"])
        else:
            links.append("")

        if img_tag and img_tag.get("src"):
            images.append(img_tag["src"])
        else:
            images.append("")

    return links, images

# 📦 Отримати назву товару
def get_product_title(html):
    soup = BeautifulSoup(html, 'html.parser')
    h1 = soup.find("h1")
    return h1.text.strip() if h1 else "Назву не вдалося знайти"


# 💲 Отримати ціну з HTML
def get_price(html):
    soup = BeautifulSoup(html, 'html.parser')
    price_tag = soup.select_one('p.price span.woocommerce-Price-amount bdi')
    return price_tag.text.strip() if price_tag else "Ціна не знайдена"




# 🖼 Отримати зображення зі сторінки
def get_image_from_html(html):
    match = re.search(r'<img[^>]+(?:data-large_image|srcset)="([^"]+)"', html, re.IGNORECASE)
    if match:
        url = match.group(1)
        if ',' in url:
            return url.split(',')[-1].strip().split(' ')[0]
        return url
    return None

# 📤 Надіслати повідомлення
def send_telegram(payload, is_photo=True):
    endpoint = "/sendPhoto" if is_photo else "/sendMessage"
    url = f"https://api.telegram.org/bot{token}{endpoint}"
    try:
        res = requests.post(url, json=payload)
        print("[✅] Відповідь Telegram:", res.json())
    except Exception as e:
        print(f"[❌] Помилка надсилання повідомлення: {e}")

# 🚀 Основна логіка
def send_new_items():
    item_links, image_links = get_latest_items()

    if not item_links:
        print("❗️ Не знайдено новинок.")
        return

    for i in range(len(item_links)):
        item_url = item_links[i].strip()
        image_url = image_links[i].strip()

        if not item_url:
            continue

        html = get_html(item_url)
        if not html:
            continue

        if not image_url:
            image_url = get_image_from_html(html)

        title = get_product_title(html)
        price = get_price(html)

        message = f"🆕 *Новинка від видавництва Підручники і посібники*\n\n*Назва:* {title}\n*Ціна:* {price}"

        payload = {
            "chat_id": chat_id,
            "parse_mode": "Markdown",
            "reply_markup": {
                "inline_keyboard": [[{"text": "Детальніше", "url": item_url}]]
            }
        }

        if image_url:
            payload["caption"] = message
            payload["photo"] = image_url
            send_telegram(payload, is_photo=True)
        else:
            payload["text"] = message
            send_telegram(payload, is_photo=False)

        time.sleep(1)  # rate-limit Telegram

    print("✅ Готово.")

# ▶️ Запуск
if __name__ == "__main__":
    send_new_items()
