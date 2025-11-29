# desktop_client/main.py
import flet as ft
import requests
import os

BACKEND_URL = "http://127.0.0.1:8000"

def main(page: ft.Page):
    page.title = "Project Bedrock"
    page.window_width = 800
    page.window_height = 600
    
    # --- UI Controls for the Dialog ---
    title_field = ft.TextField(label="Title")
    authors_field = ft.TextField(label="Authors")
    year_field = ft.TextField(label="Year (Gregorian)", width=200)
    # We need to store the original filename to send back to the backend
    original_filename_store = ft.Text(visible=False) 

    # --- "My Library" View Controls ---
    library_list_view = ft.ListView(expand=True, spacing=10, auto_scroll=True)

    def close_dialog(e):
        confirmation_dialog.open = False
        page.update()

    def confirm_ingestion(e):
        """Send final metadata to backend to be saved."""
        try:
            # Prepare the data in the format the backend expects
            request_data = {
                "original_filename": original_filename_store.value,
                "title": title_field.value,
                "authors": [author.strip() for author in authors_field.value.split(',')],
                "gregorian_year": int(year_field.value) if year_field.value.isdigit() else 0,
            }
            
            response = requests.post(f"{BACKEND_URL}/library/ingest/interactive_confirm", json=request_data, timeout=60) # Increased timeout
            response.raise_for_status()
            
            data = response.json()
            
            # Add the new document to our visible list
            library_list_view.controls.append(
                ft.ListTile(title=ft.Text(title_field.value), subtitle=ft.Text(f"{authors_field.value} ({year_field.value})"))
            )

            page.snack_bar = ft.SnackBar(ft.Text(f"Successfully ingested '{title_field.value}'!"), bgcolor=ft.Colors.GREEN)
            page.snack_bar.open = True

        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"Error during confirmation: {ex}"), bgcolor=ft.Colors.ERROR)
            page.snack_bar.open = True

        confirmation_dialog.open = False
        page.update()

    confirmation_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Confirm Metadata"),
        content=ft.Column([
            title_field,
            authors_field,
            year_field
        ]),
        actions=[
            ft.TextButton("Cancel", on_click=close_dialog),
            ft.FilledButton("Confirm", on_click=confirm_ingestion),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.overlay.append(confirmation_dialog)

    # --- Logic for handling file selection ---
    progress_ring = ft.ProgressRing(visible=False)
    
    def on_file_picked(e: ft.FilePickerResultEvent):
        if e.files:
            # Store the original filename for the confirmation step
            original_filename_store.value = os.path.basename(e.files[0].path)
            process_and_display_pdf(e.files[0].path)

    file_picker = ft.FilePicker(on_result=on_file_picked)
    page.overlay.append(file_picker)

    def process_and_display_pdf(file_path: str):
        progress_ring.visible = True
        page.update()
        
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (os.path.basename(file_path), f, 'application/pdf')}
                response = requests.post(f"{BACKEND_URL}/library/ingest/interactive_start", files=files, timeout=30)
            response.raise_for_status()

            data = response.json()
            title_field.value = data.get("title", "")
            authors_field.value = ", ".join(data.get("authors", []))
            year_field.value = data.get("gregorian_year", "")
            
            confirmation_dialog.open = True
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"Error during initial processing: {ex}"), bgcolor=ft.Colors.ERROR)
            page.snack_bar.open = True
        
        progress_ring.visible = False
        page.update()

    # --- DEFINE THE TWO MAIN VIEWS (TABS) ---
    add_document_view = ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE, size=50, color=ft.Colors.BLUE),
            ft.Text("Add a new document to your library"),
            ft.ElevatedButton("Select File", on_click=lambda _: file_picker.pick_files(
                allow_multiple=False, allowed_extensions=["pdf"]
            )),
            progress_ring
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
        expand=True
    )

    my_library_view = ft.Container(
        content=ft.Column([
            ft.Text("My Library", size=30, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            library_list_view
        ]),
        expand=True
    )

    # --- NAVIGATION LOGIC ---
    def tabs_changed(e):
        add_document_view.visible = (e.control.selected_index == 1)
        my_library_view.visible = (e.control.selected_index == 0)
        page.update()

    # THIS IS THE CORRECTED SECTION
    page.navigation_bar = ft.NavigationBar(
        selected_index=0, # Start on the "Library" tab
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.BOOK_OUTLINED, selected_icon=ft.Icons.BOOK, label="Library"),
            ft.NavigationBarDestination(icon=ft.Icons.ADD_CIRCLE_OUTLINE, selected_icon=ft.Icons.ADD_CIRCLE, label="Add"),
        ], on_change=tabs_changed
    )
    
    # Add all views to the page but only show the first one initially
    add_document_view.visible = False
    page.add(my_library_view, add_document_view)

if __name__ == "__main__":
    ft.app(target=main)