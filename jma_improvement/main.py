import requests
import json
import sqlite3
import flet as ft

# SQLite DBへの接続
conn = sqlite3.connect('weather.db')
cursor = conn.cursor()

# エリア情報のURL
AREA_URL = "https://www.jma.go.jp/bosai/common/const/area.json"

# 天気予報のURL
def fetch_weather(area_code):
    forecast_url = f"https://www.jma.go.jp/bosai/forecast/data/forecast/{area_code}.json"
    response = requests.get(forecast_url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch weather data for area code: {area_code}")
        return None

# 地域情報を取得してJSONファイルに保存
def save_area_data():
    try:
        response = requests.get(AREA_URL)
        if response.status_code == 200:
            area_data = response.json()
            with open('area_data.json', 'w', encoding='utf-8') as f:
                json.dump(area_data, f, ensure_ascii=False, indent=4)
            print("地域情報を 'area_data.json' に保存しました。")
        else:
            print("地域情報の取得に失敗しました。")
    except Exception as e:
        print(f"エラー: {e}")

# 全ての地域の天気情報を取得してall_forecasts.jsonに保存
def save_all_forecasts():
    try:
        response = requests.get(AREA_URL)
        if response.status_code == 200:
            area_data = response.json()
            all_forecasts = []

            # 地域ごとの天気情報を取得
            for center_code, center_info in area_data["centers"].items():
                for area_code in center_info["children"]:
                    print(f"Fetching weather data for area code {area_code}")
                    weather_data = fetch_weather(area_code)
                    if weather_data:
                        all_forecasts.append({
                            "area_code": area_code,
                            "weather_data": weather_data
                        })
                    else:
                        # 天気情報の取得に失敗した場合はログに出力してスキップ
                        print(f"Skipping area code {area_code} due to data fetch failure.")

            # all_forecasts.json に保存
            with open('all_forecasts.json', 'w', encoding='utf-8') as f:
                json.dump(all_forecasts, f, ensure_ascii=False, indent=4)
            print("全ての地域の天気情報を 'all_forecasts.json' に保存しました。")
        else:
            print("地域情報の取得に失敗しました。")
    except Exception as e:
        print(f"エラー: {e}")

# SQLite DBへの接続
conn = sqlite3.connect('weather.db')
cursor = conn.cursor()

# データベーステーブルを作成
def create_tables():
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS areas (
        area_id INTEGER PRIMARY KEY AUTOINCREMENT,
        area_code TEXT NOT NULL UNIQUE,
        area_name TEXT NOT NULL,
        parent_area_code TEXT
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS weather_reports (
        report_id INTEGER PRIMARY KEY AUTOINCREMENT,
        area_id INTEGER NOT NULL,
        publishing_office TEXT NOT NULL,
        report_datetime TEXT NOT NULL,
        FOREIGN KEY (area_id) REFERENCES areas(area_id)
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS time_series (
        time_series_id INTEGER PRIMARY KEY AUTOINCREMENT,
        report_id INTEGER NOT NULL,
        time_define TEXT NOT NULL,
        FOREIGN KEY (report_id) REFERENCES weather_reports(report_id)
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS weather_conditions (
        condition_id INTEGER PRIMARY KEY AUTOINCREMENT,
        time_series_id INTEGER NOT NULL,
        weather TEXT,
        pop INTEGER,
        temp INTEGER,
        wind TEXT,
        wave TEXT,
        FOREIGN KEY (time_series_id) REFERENCES time_series(time_series_id)
    )''')

    conn.commit()
    print("データベーステーブルが作成されました。")

# その他のコード（省略）


# `timeDefines`が最も多い場所の天気情報をDBに格納
def insert_data_from_json(json_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for area_data in data:
        area_code = area_data['area_code']
        cursor.execute("INSERT OR IGNORE INTO areas (area_code, area_name) VALUES (?, ?)", 
                       (area_code, area_data['weather_data'][0]['publishingOffice']))

        cursor.execute("SELECT area_id FROM areas WHERE area_code = ?", (area_code,))
        area_id = cursor.fetchone()[0]

        for weather_report in area_data['weather_data']:
            publishing_office = weather_report['publishingOffice']
            report_datetime = weather_report['reportDatetime']

            cursor.execute("INSERT INTO weather_reports (area_id, publishing_office, report_datetime) VALUES (?, ?, ?)", 
                           (area_id, publishing_office, report_datetime))
            report_id = cursor.lastrowid

            for time_series in weather_report['timeSeries']:
                # `timeDefines`が最も多い場所を選択
                most_time_defines = max(time_series['timeDefines'], key=lambda x: len(x))

                cursor.execute("INSERT INTO time_series (report_id, time_define) VALUES (?, ?)", 
                               (report_id, most_time_defines))
                time_series_id = cursor.lastrowid

                for area in time_series['areas']:
                    weather = area.get('weathers', [''])[0]
                    pop = area.get('pops', [None])[0]
                    temp = area.get('temps', [None])[0]
                    wind = area.get('winds', [''])[0]
                    wave = area.get('waves', [''])[0]

                    cursor.execute('''
                    INSERT INTO weather_conditions (time_series_id, weather, pop, temp, wind, wave) 
                    VALUES (?, ?, ?, ?, ?, ?)''', 
                    (time_series_id, weather, pop, temp, wind, wave))

    conn.commit()

# 地域をクリックした時の天気情報更新
def update_weather_info(e, page, forecasts_data, weather_info, area_code):
    weather_info.controls.clear()

    # クリックした地域に対応する天気情報を表示
    for forecast in forecasts_data:
        if forecast["area_code"] == area_code:
            weather_data = forecast["weather_data"]
            for report in weather_data:
                # 同じ天気情報が二重に追加されないように
                if report.get("reportDatetime") not in [control.text for control in weather_info.controls if isinstance(control, ft.Text)]:
                    weather_info.controls.append(
                        ft.Column([
                            ft.Text(f"地域: {area_code}"),
                            ft.Text(f"発表機関: {report['publishingOffice']}"),
                            ft.Text(f"日時: {report['reportDatetime']}"),
                            ft.Text(f"天気: {report['timeSeries'][0]['areas'][0].get('weathers', [''])[0]}"),
                            ft.Text(f"降水確率: {report['timeSeries'][0]['areas'][0].get('pops', [None])[0]}%"),
                            ft.Text(f"気温: {report['timeSeries'][0]['areas'][0].get('temps', [None])[0]}°C"),
                            ft.Text(f"風: {report['timeSeries'][0]['areas'][0].get('winds', [''])[0]}"),
                            ft.Text(f"波: {report['timeSeries'][0]['areas'][0].get('waves', [''])[0]}"),
                            ft.Divider(),
                        ])
                    )
    page.update()

# 地域のリストをクリックした時に天気情報を表示
def main(page: ft.Page):
    page.title = "天気予報アプリ"
    page.vertical_alignment = ft.MainAxisAlignment.START

    # all_forecasts.jsonとarea_data.jsonを読み込む
    with open('all_forecasts.json', 'r', encoding='utf-8') as f:
        forecasts_data = json.load(f)

    # 地域情報の取得
    with open('area_data.json', 'r', encoding='utf-8') as f:
        area_data = json.load(f)

    region_controls = []
    for center_code, center_info in area_data["centers"].items():
        # 地方ごとのExpansionTileを作成
        region_name = center_info['name']
        subregion_controls = []

        # サブタイル（都道府県）を作成
        for area_code in center_info["children"]:
            area_info = area_data["offices"].get(area_code, {})
            area_name = area_info.get("name", "不明")

            # `lambda`内で`area_code`が正しく渡されるように修正
            subregion_controls.append(
                ft.ListTile(
                    title=ft.Text(area_name),
                    on_click=lambda e, area_code=area_code: update_weather_info(e, page, forecasts_data, weather_info, area_code)
                )
            )
        
        region_controls.append(
            ft.ExpansionTile(
                title=ft.Text(region_name),
                controls=subregion_controls,
            )
        )

    # 天気情報表示エリア
    weather_info = ft.Column()

    # ページに追加するウィジェット
    page.add(
        ft.Row(
            [
                ft.Column(region_controls, expand=True),
                ft.VerticalDivider(width=1),
                weather_info,
            ],
            expand=True,
        )
    )

# 実行
if __name__ == "__main__":
    save_area_data()  # 地域情報を取得して保存
    save_all_forecasts()  # 天気予報を取得して保存

    create_tables()  # DBのテーブルを作成
    insert_data_from_json('all_forecasts.json')  # JSONデータをDBに挿入

    ft.app(target=main)  # Fletアプリを起動
