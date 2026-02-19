import flet as ft
import socket, threading, json, time

def main(page: ft.Page):
    page.title = "Darkgram Mobile"
    page.theme_mode = ft.ThemeMode.DARK
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    
    # Сокет и данные
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    my_nick = ""
    current_chat = ""

    # Элементы интерфейса
    chat_display = ft.ListView(expand=True, spacing=10, auto_scroll=True)
    typing_status = ft.Text("", size=12, color=ft.Colors.GREY_400)
    msg_input = ft.TextField(hint_text="Сообщение...", expand=True, on_change=lambda _: send_typing())
    user_list = ft.Column(scroll=ft.ScrollMode.AUTO)

    def on_message(e):
        while True:
            try:
                raw = sock.recv(2048).decode('utf-8')
                if not raw: break
                data = json.loads(raw)
                if data["type"] == "online_list":
                    update_users(data["users"])
                elif data["type"] == "msg":
                    chat_display.controls.append(ft.Text(f"{data['user']}: {data['text']}"))
                    page.update()
                elif data["type"] == "typing":
                    if data["user"] == current_chat:
                        typing_status.value = f"{data['user']} печатает..."
                        page.update()
                        time.sleep(2)
                        typing_status.value = ""
                        page.update()
            except: break

    def update_users(users):
        user_list.controls.clear()
        for u in users:
            if u != my_nick:
                user_list.controls.append(
                    ft.ListTile(title=ft.Text(u), on_click=lambda e, name=u: select_chat(name))
                )
        page.update()

    def select_chat(name):
        nonlocal current_chat
        current_chat = name
        chat_display.controls.append(ft.Divider())
        chat_display.controls.append(ft.Text(f"--- Чат с {name} ---", color=ft.Colors.BLUE_200))
        page.views.append(chat_view_page)
        page.go("/chat")

    def send_typing():
        if current_chat:
            sock.send(json.dumps({"type": "typing", "target": current_chat}).encode())

    def send_msg(e):
        if msg_input.value and current_chat:
            chat_display.controls.append(ft.Text(f"Я: {msg_input.value}", color=ft.Colors.GREEN_200))
            sock.send(json.dumps({"type": "msg", "target": current_chat, "text": msg_input.value}).encode())
            msg_input.value = ""
            page.update()

    # Страница входа
    def login_click(e):
        nonlocal my_nick
        try:
            sock.connect(("zubaf6g51.localto.net", 7416))
            my_nick = user_field.value
            sock.send(json.dumps({"type": "login", "user": my_nick, "pass": pass_field.value}).encode())
            res = json.loads(sock.recv(1024).decode())
            if res["status"] == "ok":
                threading.Thread(target=on_message, daemon=True).start()
                page.go("/users")
            else:
                page.snack_bar = ft.SnackBar(ft.Text("Ошибка входа"))
                page.snack_bar.open = True
                page.update()
        except: pass

    user_field = ft.TextField(label="Логин")
    pass_field = ft.TextField(label="Пароль", password=True, can_reveal_password=True)
    
    # Навигация
    def route_change(route):
        page.views.clear()
        page.views.append(
            ft.View("/", [ft.Text("Darkgram", size=30), user_field, pass_field, ft.ElevatedButton("Войти", on_click=login_click)])
        )
        if page.route == "/users":
            page.views.append(ft.View("/users", [ft.AppBar(title=ft.Text("Друзья онлайн")), user_list]))
        if page.route == "/chat":
            page.views.append(chat_view_page)
        page.update()

    chat_view_page = ft.View("/chat", [
        ft.AppBar(title=ft.Text("Чат")),
        chat_display,
        typing_status,
        ft.Row([msg_input, ft.IconButton(ft.Icons.SEND, on_click=send_msg)])
    ])

    page.on_route_change = route_change
    page.go(page.route)

ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=8000)
