import requests
import re
from urllib.parse import unquote


def get_person_info(name):
    """Получает расширенную информацию о личности из Википедии и Викиданных."""
    url = "https://ru.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "titles": name,
        "prop": "extracts|pageprops|pageimages|info",
        "exintro": True,
        "explaintext": True,
        "ppprop": "wikibase_item|disambiguation",
        "pithumbsize": 500,
        "piprop": "thumbnail|name",
        "redirects": True,
        "inprop": "url",
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()
        page = next(iter(data["query"]["pages"].values()))

        if "missing" in page:
            return {"error": "Статья не найдена в Википедии"}

        # Проверка на disambiguation page
        if page.get("pageprops", {}).get("disambiguation"):
            return {"error": "Это страница неоднозначности, уточните запрос"}

        wikidata_id = page.get("pageprops", {}).get("wikibase_item")
        image_url = page.get("thumbnail", {}).get("source", "")
        page_url = page.get("fullurl", "")

        if not wikidata_id:
            return {
                "full_name": page["title"],
                "summary": page.get("extract", ""),
                "image_url": unquote(image_url) if image_url else None,
                "page_url": page_url,
                "error": "Нет данных из Викиданных",
            }

        # Получаем детали из Викиданных
        wikidata_data = get_wikidata_info(wikidata_id)
        if "error" in wikidata_data:
            return wikidata_data

        wikidata_data.update({
            "summary": page.get("extract", ""),
            "image_url": unquote(image_url) if image_url else None,
            "page_url": page_url,
            "wikipedia_title": page["title"],
        })
        return wikidata_data

    except Exception as e:
        return {"error": f"Ошибка запроса: {str(e)}"}


def get_wikidata_info(wikidata_id):
    """Извлекает расширенные структурированные данные из Викиданных."""
    url = "https://www.wikidata.org/w/api.php"
    params = {
        "action": "wbgetentities",
        "format": "json",
        "ids": wikidata_id,
        "props": "labels|claims|descriptions|aliases|sitelinks",
        "languages": "ru",
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()
        entity = data["entities"][wikidata_id]

        # Проверка, что это человек (Q5)
        instance_of = [claim["mainsnak"]["datavalue"]["value"]["id"]
                       for claim in entity.get("claims", {}).get("P31", [])
                       if "datavalue" in claim["mainsnak"]]
        if "Q5" not in instance_of:
            return {"error": "Это не человек"}

        # Основные данные
        name = entity["labels"]["ru"]["value"]
        description = entity["descriptions"].get("ru", {}).get("value", "")

        # Псевдонимы/альтернативные имена
        aliases = [alias["value"] for alias in
                   entity.get("aliases", {}).get("ru", [])]

        # Даты рождения/смерти с более точным форматированием
        birth_date = format_date(
            get_claim_value(entity, "P569"))  # P569 = дата рождения
        death_date = format_date(
            get_claim_value(entity, "P570"))  # P570 = дата смерти

        # Место рождения/смерти
        birth_place = get_claim_values(entity, "P19")  # P19 = место рождения
        death_place = get_claim_values(entity, "P20")  # P20 = место смерти

        # Профессии и страны
        occupations = get_claim_values(entity,
                                       "P106")  # P106 = род деятельности
        countries = get_claim_values(entity, "P27")  # P27 = страна гражданства

        # Образование
        educations = get_claim_values(entity,
                                      "P69")  # P69 = образовательное учреждение

        # Награды
        awards = get_claim_values(entity, "P166")  # P166 = награда

        # Работы (для писателей, художников и т.д.)
        notable_works = get_claim_values(entity, "P800")  # P800 = notable work

        # Должности/позиции
        positions = get_claim_values(entity, "P39")  # P39 = должность

        # Партии/организации
        parties = get_claim_values(entity,
                                   "P102")  # P102 = член политической партии

        # Языки, на которых говорит человек
        languages = get_claim_values(entity,
                                     "P1412")  # P1412 = languages spoken, written or signed

        # Пол (Q6581097 - мужской, Q6581072 - женский)
        gender = get_claim_values(entity, "P21")  # P21 = пол

        # Этническая принадлежность
        ethnic_group = get_claim_values(entity,
                                        "P172")  # P172 = этническая принадлежность

        # Религия
        religion = get_claim_values(entity, "P140")  # P140 = религия

        # Дети
        children = get_claim_values(entity, "P40")  # P40 = ребенок

        # Сайты
        official_websites = get_external_identifiers(entity,
                                                     "P856")  # P856 = официальный сайт

        # Социальные сети и другие идентификаторы
        twitter = get_external_identifiers(entity, "P2002")
        instagram = get_external_identifiers(entity, "P2003")
        facebook = get_external_identifiers(entity, "P2013")
        youtube = get_external_identifiers(entity, "P2397")

        # IMDB ID (для актеров, режиссеров)
        imdb_id = get_external_identifiers(entity, "P345")

        # VIAF ID (международный идентификатор)
        viaf_id = get_external_identifiers(entity, "P214")

        # ISNI (International Standard Name Identifier)
        isni = get_external_identifiers(entity, "P213")

        # ORCID (для ученых)
        orcid = get_external_identifiers(entity, "P496")

        return {
            "full_name": name,
            "aliases": aliases,
            "description": description,
            "birth_date": birth_date,
            "death_date": death_date,
            "birth_place": birth_place,
            "death_place": death_place,
            "occupations": occupations,
            "countries": countries,
            "educations": educations,
            "awards": awards,
            "notable_works": notable_works,
            "positions": positions,
            "parties": parties,
            "languages": languages,
            "gender": gender,
            "ethnic_group": ethnic_group,
            "religion": religion,
            "children": children,
            "official_websites": official_websites,
            "social_media": {
                "twitter": twitter,
                "instagram": instagram,
                "facebook": facebook,
                "youtube": youtube,
            },
            "external_ids": {
                "imdb": imdb_id,
                "viaf": viaf_id,
                "isni": isni,
                "orcid": orcid,
            },
            "wikidata_id": wikidata_id,
            "wikidata_url": f"https://www.wikidata.org/wiki/{wikidata_id}",
        }
    except Exception as e:
        return {"error": f"Ошибка Викиданных: {str(e)}"}


def get_claim_value(entity, property_id):
    """Извлекает значение конкретного свойства."""
    claims = entity.get("claims", {}).get(property_id, [])
    if claims and "datavalue" in claims[0]["mainsnak"]:
        return claims[0]["mainsnak"]["datavalue"]["value"]
    return None


def get_claim_values(entity, property_id):
    """Извлекает список значений свойства."""
    values = []
    claims = entity.get("claims", {}).get(property_id, [])

    for claim in claims:
        if "datavalue" not in claim["mainsnak"]:
            continue

        datavalue = claim["mainsnak"]["datavalue"]
        if datavalue["type"] == "wikibase-entityid":
            item_id = datavalue["value"]["id"]
            label = get_wikidata_label(item_id)
            if label:
                values.append(label)
        elif datavalue["type"] == "time":
            values.append(format_date(datavalue["value"]["time"]))
        elif datavalue["type"] == "string":
            values.append(datavalue["value"])
        elif datavalue["type"] == "monolingualtext":
            values.append(datavalue["value"]["text"])

    return values


def get_external_identifiers(entity, property_id):
    """Получает внешние идентификаторы (соцсети, IMDB и т.д.)."""
    claims = entity.get("claims", {}).get(property_id, [])
    if not claims:
        return None

    values = []
    for claim in claims:
        if "datavalue" in claim["mainsnak"]:
            if claim["mainsnak"]["datavalue"]["type"] == "string":
                value = claim["mainsnak"]["datavalue"]["value"]
                # Форматируем URL для некоторых свойств
                if property_id == "P2002":  # Twitter
                    value = f"https://twitter.com/{value}"
                elif property_id == "P2003":  # Instagram
                    value = f"https://instagram.com/{value}"
                elif property_id == "P2013":  # Facebook
                    value = f"https://facebook.com/{value}"
                elif property_id == "P2397":  # YouTube
                    value = f"https://youtube.com/channel/{value}"
                elif property_id == "P856":  # Официальный сайт
                    if not value.startswith(("http://", "https://")):
                        value = f"https://{value}"
                values.append(value)

    return values[0] if len(values) == 1 else values if values else None


def get_wikidata_label(item_id):
    """Получает название элемента Викиданных на русском."""
    url = "https://www.wikidata.org/w/api.php"
    params = {
        "action": "wbgetentities",
        "ids": item_id,
        "props": "labels",
        "languages": "ru",
        "format": "json",
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()
        return data["entities"][item_id]["labels"]["ru"]["value"]
    except:
        return None


def format_date(date_info):
    time_str = date_info['time']
    precision = date_info['precision']

    # Проверяем, поддерживается ли точность (например, год, месяц, день)
    if precision not in [9, 10, 11]:
        return "Unsupported precision"

    # Разбираем строку времени
    match = re.match(r'([+-]?\d+)-(\d+)-(\d+)T.*', time_str)
    if not match:
        return "Invalid time format"

    year_str, month_str, day_str = match.groups()
    year = int(year_str)
    month = int(month_str)
    day = int(day_str)

    # Определяем эру (до н. э. или н. э.)
    era = "до н. э." if year < 1 else "н. э."
    abs_year = abs(year)

    # Форматируем в зависимости от точности
    if precision == 9:  # Год
        return f"{abs_year} {era}"
    elif precision == 10:  # Месяц
        if month == 0:
            return f"{abs_year} {era}"
        return f"{abs_year} {era}, месяц {month}"
    elif precision == 11:  # День
        if month == 0 or day == 0:
            return f"{abs_year} {era}"
        return f"{abs_year} {era}, {month}/{day}"
    else:
        return "Unsupported precision"