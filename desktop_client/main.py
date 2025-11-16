# desktop_client/main.py
import flet as ft
import requests
import os

BACKEND_URL = "http://127.0.0.1:8000"

def main(page: ft.Page):
    page.title = "Project Bedrock - Add Document"
    page.window_width = 800
    page.window_height = 600
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    # --- UI Controls for the Dialog ---
    title_field = ft.TextField(label="Title")
    authors_field = ft.TextField(label="Authors")
    year_field = ft.TextField(label="Year (Gregorian)", width=200)
    shamsi_year_field = ft.TextField(label="Year (Shamsi)", read_only=True, width=200)

    def close_dialog(e):
        confirmation_dialog.open = False
        page.update()

    confirmation_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Confirm Metadata"),
        content=ft.Column([
            ft.Text("The AI has extracted the following. Please review and edit if necessary."),
            title_field,
            authors_field,
            ft.Row([year_field, shamsi_year_field])
        ]),
        actions=[
            ft.TextButton("Cancel", on_click=close_dialog),
            ft.FilledButton("Confirm", on_click=close_dialog),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    # Add the dialog to the page's overlay so it can be shown
    page.overlay.append(confirmation_dialog)

    # --- UI Controls for the Main View ---
    progress_ring = ft.ProgressRing(visible=False)
    
    def on_file_picked(e: ft.FilePickerResultEvent):
        if e.files:
            process_and_display_pdf(e.files[0].path)

    file_picker = ft.FilePicker(on_result=on_file_picked)
    page.overlay.append(file_picker)

    # --- Main Logic ---
    def process_and_display_pdf(file_path: str):
        progress_ring.visible = True
        page.update()

        try:
            with open(file_path, 'rb') as f:
                files = {'file': (os.path.basename(file_path), f, 'application/pdf')}
                response = requests.post(f"{BACKEND_URL}/library/ingest/interactive_start", files=files, timeout=30)

            response.raise_for_status() # This will raise an error for 4xx or 5xx responses

            data = response.json()
            title_field.value = data.get("title", "")
            authors_field.value = ", ".join(data.get("authors", []))
            year_field.value = data.get("gregorian_year", "")
            shamsi_year_field.value = data.get("shamsi_year", "")
            
            confirmation_dialog.open = True

        except requests.exceptions.HTTPError as http_err:
            detail = f"HTTP Error: {http_err}"
            try:
                detail = response.json().get('detail', str(http_err))
            except:
                pass
            page.snack_bar = ft.SnackBar(ft.Text(detail), bgcolor=ft.Colors.ERROR)
            page.snack_bar.open = True
        except requests.exceptions.ConnectionError:
            page.snack_bar = ft.SnackBar(ft.Text("Connection Error: Backend is not running."), bgcolor=ft.Colors.ERROR)
            page.snack_bar.open = True
        except Exception as e:
            page.snack_bar = ft.SnackBar(ft.Text(f"An error occurred: {e}"), bgcolor=ft.Colors.ERROR)
            page.snack_bar.open = True
        
        progress_ring.visible = False
        page.update()
        
    # --- Page Layout ---
    page.add(
        ft.Column([
            ft.Text("Add a New Document", size=30, weight=ft.FontWeight.BOLD),
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.UPLOAD_FILE_ROUNDED, size=50, color=ft.Colors.BLUE),
                    ft.Text("Drag & Drop is disabled for now. Please use the button.", size=16),
                    ft.ElevatedButton("Select File", on_click=lambda _: file_picker.pick_files(
                        allow_multiple=False, allowed_extensions=["pdf"]
                    )),
                    progress_ring
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
                height=400, width=600,
                alignment=ft.alignment.center,
                border=ft.border.all(1, ft.Colors.GREY_700),
                border_radius=ft.border_radius.all(10),
            )
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True)
    )

if __name__ == "__main__":
    ft.app(target=main)