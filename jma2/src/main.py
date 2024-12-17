import flet as ft
import requests
import sqlite3

class WeatherApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.create_database()
        self.regions = self.load_areas()  # 地域情報を読み込み
        
        # UIコンポーネントの作成
        self.region_dropdown = ft.Dropdown(
            label="Select Region",
            options=[
                ft.dropdown.Option(child_code, f"{center_info['name']} - {child_code}")
                for center_info in self.regions for child_code in center_info['children']
            ],
            on_change=self.region_selected
        )
        
        self.weather_info = ft.Column()
        self.initialize()

    def create_database(self):
        """SQLiteデータベースとテーブルを作成。"""
        conn = sqlite3.connect('weather_forecast.db')
        cursor = conn.cursor()

        # areas テーブルの作成
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS areas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE,
                name TEXT
            )
        ''')

        # weather_forecast テーブルの作成
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS weather_forecast (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                area_id INTEGER,
                forecast_date DATE,
                weather TEXT,
                temperature REAL,
                wind TEXT,
                precipitation_probability INTEGER,
                FOREIGN KEY (area_id) REFERENCES areas(id)
            )
        ''')

        conn.commit()
        conn.close()

    def load_areas(self):
        """外部の地域情報JSONをロードする。"""
        try:
            response = requests.get("http://www.jma.go.jp/bosai/common/const/area.json")
            data = response.json()
            regions = []

            # 中心部地域（centers）から情報を取得
            for center_code, center_info in data["centers"].items():
                region = {
                    "name": center_info["name"],
                    "children": center_info["children"]
                }
                regions.append(region)

            return regions
        except Exception as e:
            print(f"Failed to load areas: {e}")
            return []

    def initialize(self):
        """初期UI構成を作成する。"""
        self.page.add(
            ft.Column([
                self.region_dropdown,
                ft.Divider(),
                self.weather_info
            ])
        )
    
    def store_area(self, code, name):
        """エリア情報をDBに格納する。"""
        conn = sqlite3.connect('weather_forecast.db')
        cursor = conn.cursor()

        cursor.execute('INSERT OR IGNORE INTO areas (code, name) VALUES (?, ?)', (code, name))
        conn.commit()
        conn.close()

    def store_forecast(self, area_id, forecast_date, weather, temperature, wind, precipitation_probability):
        """天気予報情報をDBに格納する。"""
        conn = sqlite3.connect('weather_forecast.db')
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO weather_forecast (area_id, forecast_date, weather, temperature, wind, precipitation_probability) 
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (area_id, forecast_date, weather, temperature, wind, precipitation_probability))

        conn.commit()
        conn.close()

    def fetch_weather_forecast(self, area_code):
        """指定された地域コードの天気予報を取得。"""
        try:
            url = f"https://www.jma.go.jp/bosai/forecast/data/forecast/{area_code}.json"
            response = requests.get(url)

            if response.status_code == 200:
                # レスポンスの内容をデバッグ用に出力
                print("API Response:", response.json())
                return response.json()
            else:
                print(f"Error fetching data for {area_code}: {response.status_code}")
                return None
        except Exception as e:
            print(f"Exception occurred: {e}")
            return None

    def store_weather_data(self, area_code, weather_data):
        """APIから取得した天気データをDBに格納。"""
        for forecast in weather_data:
            # 'areas'キーが存在するか確認
            if 'areas' in forecast:
                area_name = forecast['areas'][0]['area']['name']
                forecast_date = forecast['reportDatetime']
                weathers = forecast['timeSeries'][0]['areas'][0]['weathers']
                temperature = forecast['timeSeries'][0]['areas'][0]['temps'][0]
                wind = forecast['timeSeries'][0]['areas'][0]['winds'][0]
                precipitation_probability = forecast['timeSeries'][0]['areas'][0]['pops'][0]

                # エリアコードをDBに保存
                self.store_area(area_code, area_name)

                # エリアIDを取得
                conn = sqlite3.connect('weather_forecast.db')
                cursor = conn.cursor()
                cursor.execute('SELECT id FROM areas WHERE code = ?', (area_code,))
                area_id = cursor.fetchone()[0]
                conn.close()

                # 天気情報をDBに格納
                self.store_forecast(area_id, forecast_date, weathers[0], temperature, wind, precipitation_probability)
            else:
                print(f"Warning: 'areas' key not found in forecast data: {forecast}")

    def region_selected(self, e):
        """地域が選択されたときの処理。"""
        area_code = e.control.value
        weather_data = self.fetch_weather_forecast(area_code)

        if weather_data:
            self.store_weather_data(area_code, weather_data)
            self.display_weather(weather_data)
        else:
            self.weather_info.controls.append(ft.Text("Failed to fetch weather data."))
            self.page.update()

    def display_weather(self, weather_data):
        """取得した天気データを表示。"""
        self.weather_info.controls.clear()  # 古い情報をクリア

        for forecast in weather_data:
            publishing_office = forecast.get("publishingOffice", "情報なし")
            report_datetime = forecast.get("reportDatetime", "情報なし")
            time_series = forecast['timeSeries']

            for series in time_series:
                areas = series.get('areas', [])
                for area in areas:
                    area_name = area['area']['name']
                    
                    # 天気情報を抽出
                    weathers = area.get('weathers', ["情報なし"])
                    wind_info = area.get('winds', ["情報なし"])
                    pops = area.get('pops', ["情報なし"])
                    temps = area.get('temps', ["情報なし"])

                    self.weather_info.controls.append(
                        ft.Text(f"{area_name} - {report_datetime}: 天気: {', '.join(weathers)} | "
                                f"風: {', '.join(wind_info)} | "
                                f"降水確率: {', '.join(pops)}% | "
                                f"気温: {', '.join(temps)} °C")
                    )

        self.page.update()

def main(page: ft.Page):
    page.title = "Weather Forecast App"
    page.theme = ft.Theme(font_family="Verdana")
    app = WeatherApp(page)

ft.app(target=main, assets_dir="../assets")