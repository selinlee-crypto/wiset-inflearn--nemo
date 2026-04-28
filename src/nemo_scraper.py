import requests
import sqlite3
import os
import time
import json
import csv

# 수집할 전체 필드 리스트
ALL_FIELDS = [
    'agentId', 'areaPrice', 'articleType', 'buildingManagementSerialNumber', 
    'businessLargeCode', 'businessLargeCodeName', 'businessMiddleCode', 
    'businessMiddleCodeName', 'completionConfirmedDateUtc', 'confirmedDateUtc', 
    'createdDateUtc', 'deposit', 'editedDateUtc', 'favoriteCount', 
    'firstDeposit', 'firstMonthlyRent', 'firstPremium', 'floor', 
    'groundFloor', 'id', 'isInYourFavorited', 'isMoveInDate', 
    'isPremiumClosed', 'isPriority', 'maintenanceFee', 'monthlyRent', 
    'moveInDate', 'nearSubwayStation', 'number', 'originPhotoUrls', 
    'premium', 'previewPhotoUrl', 'priceType', 'priceTypeName', 
    'sale', 'size', 'smallPhotoUrls', 'state', 'title', 'viewCount'
]

def setup_database(db_path):
    """SQLite 데이터베이스 및 테이블 생성"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 동적으로 컬럼 정의 생성
    columns_def = []
    for field in ALL_FIELDS:
        if field == 'id':
            columns_def.append(f"{field} TEXT PRIMARY KEY")
        elif field in ['number', 'articleType', 'deposit', 'monthlyRent', 'premium', 'sale', 'maintenanceFee', 'floor', 'groundFloor', 'viewCount', 'favoriteCount', 'state', 'businessLargeCode', 'businessMiddleCode', 'priceType']:
            columns_def.append(f"{field} INTEGER")
        elif field in ['size', 'areaPrice', 'firstDeposit', 'firstMonthlyRent', 'firstPremium']:
            columns_def.append(f"{field} REAL")
        else:
            columns_def.append(f"{field} TEXT")
            
    sql = f"CREATE TABLE IF NOT EXISTS nemo_items ({', '.join(columns_def)})"
    cursor.execute(sql)
    conn.commit()
    return conn

def fetch_data(page_index):
    """Nemo API에서 데이터 가져오기"""
    url = "https://www.nemoapp.kr/api/store/search-list"
    params = {
        "Subway": "222",
        "Radius": "1000",
        "CompletedOnly": "false",
        "NELat": "37.502378628641274",
        "NELng": "127.04326946065672",
        "SWLat": "37.49688481053153",
        "SWLng": "127.03639072777788",
        "Zoom": "15",
        "SortBy": "29",
        "PageIndex": str(page_index)
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    response = requests.get(url, params=params, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching page {page_index}: {response.status_code}")
        return None

def save_items(conn, items):
    """데이터베이스에 아이템 저장 (평탄화 포함)"""
    cursor = conn.cursor()
    
    placeholders = ', '.join(['?' for _ in ALL_FIELDS])
    fields_str = ', '.join(ALL_FIELDS)
    sql = f"INSERT OR REPLACE INTO nemo_items ({fields_str}) VALUES ({placeholders})"
    
    for item in items:
        data = []
        for field in ALL_FIELDS:
            val = item.get(field)
            # 리스트 형태의 데이터(사진 URL 등)는 문자열로 변환하여 평탄화
            if isinstance(val, list):
                val = ",".join(val) if val else ""
            data.append(val)
        
        cursor.execute(sql, tuple(data))
    conn.commit()

def export_to_csv(db_path, csv_path):
    """데이터베이스 내용을 CSV로 내보내기"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM nemo_items")
    rows = cursor.fetchall()
    
    if rows:
        with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            for row in rows:
                writer.writerow(dict(row))
        print(f"CSV exported to: {csv_path}")
    conn.close()

def main():
    # 경로 설정
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, 'data', 'nemo_data.db')
    csv_path = os.path.join(base_dir, 'data', 'nemo_items.csv')
    
    if not os.path.exists(os.path.join(base_dir, 'data')):
        os.makedirs(os.path.join(base_dir, 'data'))
        
    conn = setup_database(db_path)
    
    page = 0
    total_collected = 0
    
    while True:
        print(f"Fetching page {page}...")
        result = fetch_data(page)
        
        if not result or 'items' not in result or not result['items']:
            print("No more items or error occurred.")
            break
            
        items = result['items']
        save_items(conn, items)
        
        count = len(items)
        total_collected += count
        print(f"Successfully saved {count} items from page {page}. (Total: {total_collected})")
        
        page += 1
        time.sleep(1) # 서버 부하 방지
        
    conn.close()
    
    # CSV 내보내기
    export_to_csv(db_path, csv_path)
    print(f"Finished. Total items collected: {total_collected}")

if __name__ == "__main__":
    main()

