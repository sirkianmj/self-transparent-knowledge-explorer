# desktop_client/main.py
import flet as ft

def main(page: ft.Page):
    page.title = "Project Bedrock"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    page.add(
        ft.Row(
            [
                ft.Text("Welcome to the Self-Transparent Knowledge Explorer", size=20)
            ],
            alignment=ft.MainAxisAlignment.CENTER
        )
    )

if __name__ == "__main__":
    ft.app(target=main)