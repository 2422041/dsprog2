import flet as ft
import requests
import json


def load_areas():
    with open('jma/areas.json', 'r', encoding='utf-8') as file:
        data = json.load(file)
        return data['centers']


def fetch_weather_forecast(area_code):
    url = f"https://www.jma.go.jp/bosai/forecast/data/forecast/{area_code}.json"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"{area_code}の天気情報の取得に失敗しました")


def display_weather(page_content, weather_data):
    page_content.controls.clear() 

    if weather_data and isinstance(weather_data, list) and len(weather_data) > 0:
        forecasts = weather_data[0]['timeSeries'][0]['areas']  

        for forecast in forecasts:
            date_label = weather_data[0]['timeSeries'][0]['timeDefines'][0] 
            weather = forecast.get('weather', '情報なし')
            temperature_max = forecast.get('temperature', {}).get('max', {}).get('celsius', '不明')
            temperature_min = forecast.get('temperature', {}).get('min', {}).get('celsius', '不明')

            card = ft.Card(
                content=ft.Column([
                    ft.Row([
                        ft.Text(f"{forecast['area']['name']}: {date_label}", size=ft.TextSize.LARGE),
                        ft.Text(weather, size=ft.TextSize.SMALL),
                    ]),
                    ft.Row([
                        ft.Text(f"気温: 最低 {temperature_min} °C / 最高 {temperature_max} °C"),
                    ]),
                ]),
                padding=10,
                margin=5,
                elevation=2,
            )
            page_content.controls.append(card)

    page_content.update()  


def main(page: ft.Page):
    page.title = "天気予報アプリ"
    page.vertical_alignment = ft.MainAxisAlignment.START

    areas_data = load_areas() 
    region_list = areas_data 

    
    page.add(ft.AppBar(title=ft.Text("天気予報アプリ")))

    
    region_tiles = ft.ListView()

    for region_code, region_info in region_list.items():
        region_name = region_info['name']  
        region_children = region_info['children']  
        
        region_tiles.controls.append(
            ft.ListTile(
                title=ft.Text(region_name),
                on_click=lambda e, code=region_code: handle_region_select(code, page_content),
            )
        )

  
    page_content = ft.Column()
    page.add(
        ft.Row(
            [
                region_tiles,
                ft.VerticalDivider(width=1),
                page_content,
            ],
            expand=True,
        )
    )

    def handle_region_select(area_code, page_content):
        weather_data = fetch_weather_forecast(area_code)
        display_weather(page_content, weather_data)

ft.app(main)