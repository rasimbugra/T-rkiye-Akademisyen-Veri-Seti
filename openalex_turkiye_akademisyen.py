#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenAlex ile Türkiye'deki üniversitelere bağlı akademisyen verisi toplama.

Gereksinimler:
    pip install requests pandas openpyxl

Kullanım:
    1) https://openalex.org/settings/api adresinden ÜCRETSİZ API anahtarı al
       (Şubat 2026'dan beri anahtar zorunlu).
    2) Anahtarı ortam değişkeni olarak tanımla:
         Windows (PowerShell):  $env:OPENALEX_API_KEY="anahtarin"
         Mac/Linux:             export OPENALEX_API_KEY="anahtarin"
    3) Çalıştır:
         python openalex_turkiye_akademisyen.py --min-works 5
       İlk denemede küçük test için:
         python openalex_turkiye_akademisyen.py --max-authors 1000

Özellikler:
  - Cursor tabanlı sayfalama (200 kayıt/sayfa)
  - Her 500 kayıtta CSV'ye append + imleç (cursor) kaydı -> kesintide kaldığı yerden devam
  - Hata yönetimi: retry + log dosyası, script çökmez
  - İsteğe bağlı: her yazar için en çok atıf alan N makalenin adı (--with-works)
  - Sonunda CSV -> Excel dönüşümü
"""

import argparse
import csv
import json
import logging
import os
import random
import sys
import time

import pandas as pd
import requests

BASE_URL = "https://api.openalex.org"
CSV_FILE = "openalex_tr_akademisyen.csv"
XLSX_FILE = "openalex_tr_akademisyen.xlsx"
STATE_FILE = "openalex_state.json"
LOG_FILE = "openalex_hatalar.log"
BATCH_SIZE = 500
PER_PAGE = 200

COLUMNS = [
    "OpenAlex_ID", "Ad_Soyad", "Profil_URL", "ORCID",
    "Universite_Adi", "Kurum_Turu",
    "Arastirma_Alanlari", "Makale_Sayisi", "Atif_Sayisi", "H_Index",
    "Alternatif_Isimler", "Makale_Adlari",
]

logging.basicConfig(
    filename=LOG_FILE, level=logging.WARNING,
    format="%(asctime)s | %(levelname)s | %(message)s", encoding="utf-8",
)
session = requests.Session()
session.headers.update({"User-Agent": "akademik-veri-arastirma/1.0 (mailto:merve_basak64@hotmail.com)"})


def api_get(path, params, retries=5):
    """Hata durumunda üstel bekleme ile tekrar dener; başaramazsa None döner."""
    url = f"{BASE_URL}/{path}"
    for attempt in range(1, retries + 1):
        try:
            r = session.get(url, params=params, timeout=60)
            if r.status_code == 200:
                return r.json()
            if r.status_code in (429, 500, 502, 503, 504):
                wait = min(2 ** attempt, 60) + random.random()
                logging.warning("HTTP %s, %.1fs bekleniyor (%s)", r.status_code, wait, url)
                time.sleep(wait)
                continue
            if r.status_code in (401, 403):
                logging.error("Yetki hatası %s: %s", r.status_code, r.text[:300])
                print("API anahtarı hatalı/eksik veya günlük kredi doldu:", r.text[:200])
                sys.exit(1)
            logging.warning("HTTP %s: %s", r.status_code, r.text[:300])
            return None
        except requests.RequestException as e:
            wait = min(2 ** attempt, 60)
            logging.warning("Bağlantı hatası (%s): %s", url, e)
            time.sleep(wait)
    return None


def top_works(author_id, api_key, n):
    """Yazarın en çok atıf alan n makalesinin başlıkları."""
    short_id = author_id.rsplit("/", 1)[-1]
    data = api_get("works", {
        "filter": f"authorships.author.id:{short_id}",
        "sort": "cited_by_count:desc",
        "per_page": n,
        "api_key": api_key,
    })
    if not data:
        return ""
    return " | ".join((w.get("display_name") or "").strip() for w in data.get("results", []))


def parse_author(a, api_key, works_n):
    insts = a.get("last_known_institutions") or []
    topics = a.get("topics") or []
    stats = a.get("summary_stats") or {}
    row = {
        "OpenAlex_ID": a.get("id", ""),
        "Ad_Soyad": a.get("display_name", ""),
        "Profil_URL": a.get("id", ""),
        "ORCID": a.get("orcid") or "",
        "Universite_Adi": " | ".join(i.get("display_name", "") for i in insts),
        "Kurum_Turu": " | ".join(i.get("type", "") for i in insts),
        "Arastirma_Alanlari": " | ".join(t.get("display_name", "") for t in topics[:8]),
        "Makale_Sayisi": a.get("works_count", 0),
        "Atif_Sayisi": a.get("cited_by_count", 0),
        "H_Index": stats.get("h_index", ""),
        "Alternatif_Isimler": " | ".join((a.get("display_name_alternatives") or [])[:5]),
        "Makale_Adlari": "",
    }
    if works_n > 0:
        row["Makale_Adlari"] = top_works(a["id"], api_key, works_n)
    return row


def flush(buffer):
    """Tamponu CSV'ye ekler (append)."""
    if not buffer:
        return
    new_file = not os.path.exists(CSV_FILE)
    with open(CSV_FILE, "a", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        if new_file:
            w.writeheader()
        w.writerows(buffer)
    buffer.clear()


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"cursor": "*", "total": 0}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-works", type=int, default=5,
                    help="En az bu kadar yayını olan yazarlar (varsayılan 5)")
    ap.add_argument("--max-authors", type=int, default=0,
                    help="Test için üst sınır (0 = sınırsız)")
    ap.add_argument("--with-works", type=int, default=0,
                    help="Her yazar için en çok atıf alan N makale adı (ek API isteği yapar)")
    ap.add_argument("--all-institution-types", action="store_true",
                    help="Sadece üniversite (education) değil, tüm kurum türleri")
    ap.add_argument("--restart", action="store_true", help="Kaldığı yerden değil, baştan başla")
    args = ap.parse_args()

    api_key = os.environ.get("OPENALEX_API_KEY")
    if not api_key:
        print("HATA: OPENALEX_API_KEY ortam değişkeni tanımlı değil.")
        sys.exit(1)

    if args.restart:
        for p in (STATE_FILE, CSV_FILE):
            if os.path.exists(p):
                os.remove(p)

    filters = ["last_known_institutions.country_code:TR", f"works_count:>{args.min_works - 1}"]
    if not args.all_institution_types:
        filters.append("last_known_institutions.type:education")
    filter_str = ",".join(filters)

    state = load_state()
    cursor, total = state["cursor"], state["total"]
    buffer = []
    print(f"Başlıyor. Filtre: {filter_str} | Devam noktası: {total} kayıt")

    while cursor:
        data = api_get("authors", {
            "filter": filter_str,
            "per_page": PER_PAGE,
            "cursor": cursor,
            "api_key": api_key,
        })
        if data is None:
            logging.error("Sayfa alınamadı, cursor=%s. Durum kaydedilip çıkılıyor.", cursor)
            flush(buffer)
            save_state({"cursor": cursor, "total": total})
            print("Sayfa alınamadı; tekrar çalıştırırsan kaldığı yerden devam eder.")
            break

        results = data.get("results", [])
        if not results:
            break

        for a in results:
            try:
                buffer.append(parse_author(a, api_key, args.with_works))
            except Exception as e:  # tek bir kayıt tüm işi durdurmasın
                logging.error("Yazar işlenemedi %s: %s", a.get("id"), e)
            if args.with_works:
                time.sleep(random.uniform(0.05, 0.2))

        cursor = (data.get("meta") or {}).get("next_cursor")
        total += len(results)

        if len(buffer) >= BATCH_SIZE:
            flush(buffer)
            save_state({"cursor": cursor, "total": total})
            print(f"{total} kayıt kaydedildi...")

        if args.max_authors and total >= args.max_authors:
            break
        time.sleep(random.uniform(0.1, 0.4))

    flush(buffer)
    save_state({"cursor": cursor, "total": total})

    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE, encoding="utf-8-sig")
        df = df.drop_duplicates(subset="OpenAlex_ID")
        df.to_csv(CSV_FILE, index=False, encoding="utf-8-sig")
        df.to_excel(XLSX_FILE, index=False)
        print(f"Bitti. {len(df)} benzersiz yazar -> {CSV_FILE}, {XLSX_FILE}")
    print(f"Hatalar için: {LOG_FILE}")


if __name__ == "__main__":
    main()
