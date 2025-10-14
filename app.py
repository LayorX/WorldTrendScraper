import os
import json
from flask import Flask, render_template, request
from math import ceil

# 從中央設定檔導入所有資料來源設定
from config import SOURCES

app = Flask(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

class Pagination:
    """一個簡單的分頁物件"""
    def __init__(self, page, per_page, total_count, items):
        self.page = page
        self.per_page = per_page
        self.total_count = total_count
        self.items = items

    @property
    def pages(self):
        return ceil(self.total_count / self.per_page)

    @property
    def has_prev(self):
        return self.page > 1

    @property
    def has_next(self):
        return self.page < self.pages

    def iter_pages(self, left_edge=2, left_current=2, right_current=5, right_edge=2):
        last = 0
        for num in range(1, self.pages + 1):
            if num <= left_edge or \
               (num > self.page - left_current - 1 and num < self.page + right_current) or \
               num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num

def get_paginated_data(raw_data, slug):
    """從原始資料中進行分頁"""
    if not raw_data:
        return None

    all_items = raw_data.get('trends', [])

    per_page = request.args.get('per_page', 10, type=int)
    page_param = f"{slug}_page"
    page = request.args.get(page_param, 1, type=int)
    
    total_count = len(all_items)
    start = (page - 1) * per_page
    end = start + per_page
    items_on_page = all_items[start:end]

    pagination = Pagination(page, per_page, total_count, items_on_page)
    return pagination

@app.route('/')
def index():
    """主頁，在每次請求時讀取所有資料並渲染模板"""
    all_data = []
    print("🔄 正在為此請求載入資料...")
    for source in SOURCES:
        raw_data = None
        filename = source['filename']
        try:
            with open(os.path.join(DATA_DIR, filename), 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
                print(f"  ✅ 已載入: {filename}")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"  ❌ 載入失敗: {filename} ({e})")

        pagination = get_paginated_data(raw_data, source['id'])
        
        if raw_data and pagination:
            all_data.append({
                "name": source['name'],
                "slug": source['id'],
                "icon": source['icon'],
                "updated": raw_data.get('updated', '1970-01-01'),
                "pagination": pagination
            })
    
    print("✨ 資料載入完成!")
    # 根據更新時間對來源進行排序，最新的在前
    sorted_data = sorted(all_data, key=lambda item: item['updated'], reverse=True)
    
    # 獲取全域 per_page 設定
    per_page_options = [5, 10, 20, 30, 50]
    current_per_page = request.args.get('per_page', 10, type=int)

    return render_template(
        'index.html', 
        sorted_data=sorted_data, 
        sources=sorted_data, # 側邊欄使用
        per_page_options=per_page_options,
        current_per_page=current_per_page,
        args=request.args # 用於構建分頁連結
    )

# No longer load data at startup
# load_data_into_cache()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)