import requests
import json
import time

# エリア情報を取得するURL
area_url = "https://www.jma.go.jp/bosai/common/const/area.json"

# 天気予報APIから天気データを取得する関数（再試行ロジックとタイムアウト設定を追加）
def fetch_weather(area_code, retries=3, delay=5):
    forecast_url = f"https://www.jma.go.jp/bosai/forecast/data/forecast/{area_code}.json"
    for attempt in range(retries):
        try:
            response = requests.get(forecast_url, timeout=10)  # 10秒のタイムアウト
            response.raise_for_status()  # ステータスコードが200以外なら例外を発生させる
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                print("Max retries reached. Could not fetch weather data.")
                return None

# エリア情報を取得しJSONファイルに保存する関数
def fetch_area_info():
    # エリア情報を取得
    response = requests.get(area_url)
    if response.status_code == 200:
        area_data = response.json()

        # 全てのエリアコードをリストアップ
        area_codes = []
        for center_info in area_data["centers"].values():
            children = center_info.get("children", [])
            area_codes.extend(children)  # 子エリアコードを追加

        print(f"全てのエリアコードの数: {len(area_codes)}")

        # 各エリアの天気情報を取得
        all_weather_data = []
        for area_code in area_codes:
            print(f"エリアコード {area_code} の天気情報を取得中...")
            weather_data = fetch_weather(area_code)
            if weather_data:
                all_weather_data.append({
                    "area_code": area_code,
                    "weather_data": weather_data
                })

        # 取得した天気情報をall_forecasts.jsonに保存
        all_forecasts_filename = "all_forecasts.json"
        with open(all_forecasts_filename, 'w', encoding='utf-8') as f:
            json.dump(all_weather_data, f, ensure_ascii=False, indent=4)
        
        print(f"全ての地域の天気情報を {all_forecasts_filename} に保存しました。")
    else:
        print("Failed to fetch area information")

# 実行
fetch_area_info()
