import requests
import json
import os

# エリア情報を取得するURL
area_url = "https://www.jma.go.jp/bosai/common/const/area.json"

# 気象庁の天気予報を取得する関数
def fetch_weather(area_code):
    # 天気予報APIのURL
    forecast_url = f"https://www.jma.go.jp/bosai/forecast/data/forecast/{area_code}.json"
    
    # APIからデータを取得
    response = requests.get(forecast_url)
    if response.status_code == 200:
        weather_data = response.json()
        return weather_data
    else:
        print(f"Failed to fetch weather data for area code {area_code}")
        return None

# Unicodeエスケープシーケンスを通常の文字に戻す関数
def decode_unicode_escape(text):
    # Unicodeエスケープシーケンスをデコード
    return text.encode('utf-8').decode('unicode_escape')

# エリア情報を取得して表示
def fetch_area_info():
    response = requests.get(area_url)
    if response.status_code == 200:
        area_data = response.json()

        print("=== エリア情報 ===")
        # エリア情報を表示
        for area_code, area_info in area_data["centers"].items():
            area_name = area_info["name"]
            print(f"エリア名: {area_name} | エリアコード: {area_code}")
        
        # 広島県の天気予報を取得
        hiroshima_area_code = "340000"
        weather_data = fetch_weather(hiroshima_area_code)

        if weather_data:
            print("\n=== 広島県の天気予報 ===")
            for report in weather_data:
                # 観測した気象台と報告日時
                publishing_office = report["publishingOffice"]
                report_datetime = report["reportDatetime"]
                print(f"\n観測した気象台: {publishing_office}, 報告日時: {report_datetime}")

                # 時間毎の天気情報
                for time_series in report["timeSeries"]:
                    time_defines = time_series["timeDefines"]
                    for area in time_series["areas"]:
                        area_name = area["area"]["name"]
                        area_code = area["area"]["code"]

                        # 天気のコードと説明を表示（Unicodeエスケープをデコード）
                        weather_codes = area.get("weatherCodes", [])
                        weather_descriptions = area.get("weathers", [])
                        
                        # 天気説明を一つ一つデコード
                        weather_descriptions = [decode_unicode_escape(desc) for desc in weather_descriptions]

                        print(f"エリア: {area_name}, 天気コード: {weather_codes}, 天気説明: {weather_descriptions}")

                        # 必要な他の情報を追加で表示することも可能
                        # 例えば降水確率など
                        if "pops" in area:
                            pops = area["pops"]
                            print(f"降水確率: {pops}")

                        if "temps" in area:
                            temps = area["temps"]
                            print(f"予想気温: {temps}")
            
            # 天気情報をJSONファイルに保存
            filename = f"forecast_{hiroshima_area_code}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(weather_data, f, ensure_ascii=False, indent=4)
            print(f"\n天気情報を {filename} に保存しました。")
        else:
            print("天気予報のデータが取得できませんでした。")
    else:
        print("Failed to fetch area information")

# 実行
fetch_area_info()






