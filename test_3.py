import requests
import json
import flet as ft

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

# JSONファイルを読み込む関数
def load_json(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

# 地域選択の更新処理
def update_weather_info(e, page, forecasts_data, weather_info, area_code):
    # 地域の天気情報を取得
    selected_weather = next(
        (data for data in forecasts_data if data["area_code"] == area_code), None
    )

    # 既存の天気情報を削除してから新しい情報を表示
    weather_info.controls.clear()

    if selected_weather is None:
        weather_info.controls.append(ft.Text("天気情報が見つかりません。"))
    else:
        weather_info.controls.append(ft.Text(f"観測した気象台: {selected_weather['weather_data'][0]['publishingOffice']}"))
        weather_info.controls.append(ft.Text(f"報告日時: {selected_weather['weather_data'][0]['reportDatetime']}"))

        # 最も多いtimeDefines数を持つtimeSeriesを選ぶ
        max_time_series = max(selected_weather["weather_data"][0]["timeSeries"], key=lambda ts: len(ts["timeDefines"]))

        # 時系列データを解析
        for area in max_time_series["areas"]:
            area_name = area["area"]["name"]
            weather_descriptions = area.get("weathers", [])
            pops = area.get("pops", [])
            temps = area.get("temps", [])

            # エリア名を表示
            weather_info.controls.append(ft.Text(f"エリア: {area_name}"))

            # 天気（weathers）情報があれば表示
            if weather_descriptions:
                weather_info.controls.append(ft.Text(f"天気: {', '.join(weather_descriptions)}"))

            # 降水確率（pops）情報があれば表示
            if pops:
                weather_info.controls.append(ft.Text(f"降水確率: {', '.join(map(str, pops))}%"))

            # 気温（temps）情報があれば表示
            if temps:
                weather_info.controls.append(ft.Text(f"予想気温: {', '.join(map(str, temps))}°C"))

    page.update()

# Fletアプリのメイン関数
def main(page: ft.Page):
    page.spacing = 0
    page.padding = 0

    # all_forecasts.jsonとarea_data.jsonを読み込む
    forecasts_data = load_json('all_forecasts.json')
    area_data = load_json('area_data.json')

    # 地域情報の取得
    region_controls = []
    for center_code, center_info in area_data["centers"].items():
        # 地方ごとのExpansionTileを作成
        region_name = center_info['name']
        subregion_controls = []

        # サブタイル（都道府県）を作成
        for area_code in center_info["children"]:
            # offices から詳細情報を取得
            area_info = area_data["offices"].get(area_code, {})
            area_name = area_info.get("name", "不明")
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


# 実行前に必要なファイルを生成
if __name__ == "__main__":
    # 地域情報と天気情報を保存
    save_area_data()
    save_all_forecasts()

    # Flet アプリを起動
    ft.app(target=main)

