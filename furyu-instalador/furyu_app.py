#!/usr/bin/env python3
"""Janela Furyu.

Conversa em português. O modo local usa o Ollama em 127.0.0.1:11434
com o modelo amadeus-verbo, sem conta e sem telemetria. O modo online
é opcional e só envia a chave de API quando está selecionado.
Não é o editor completo.
"""

import json
import threading
import urllib.error
import urllib.request

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk

OLLAMA_TAGS_URL = "http://127.0.0.1:11434/api/tags"
OLLAMA_CHAT_URL = "http://127.0.0.1:11434/api/chat"
OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"
MODEL_NAME = "amadeus-verbo"
ONLINE_MODEL = "gpt-4o-mini"
MSG_MODELO_AUSENTE = (
    "Modelo local não encontrado. Verifique se o Ollama está rodando "
    "ou mude para o modo Online."
)
SYSTEM_PROMPT = (
    "Você é o Furyu. Responda sempre em português do Brasil, "
    "de forma clara e curta."
)
WELCOME = (
    "Bem-vindo ao Furyu. No modo local, a conversa fica neste computador: "
    "o Ollama usa o modelo amadeus-verbo, sem conta e sem telemetria. "
    "No modo online, opcional, a mesma janela envia a mensagem à OpenAI "
    "somente se você escolher Online e informar a chave. "
    "Dá para trocar o modo nesta janela, sem reiniciar. "
    "Esta versão não é o editor completo."
)


def ui(callback):
    def wrapper():
        callback()
        return False

    GLib.idle_add(wrapper)


def ollama_has_model():
    try:
        with urllib.request.urlopen(OLLAMA_TAGS_URL, timeout=3) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return False
    for item in payload.get("models") or []:
        for key in ("name", "model"):
            raw = item.get(key) or ""
            if raw.split(":", 1)[0] == MODEL_NAME:
                return True
    return False


def ollama_chat(messages):
    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + messages,
        "stream": False,
        "options": {"temperature": 0.7, "num_predict": 384},
    }
    request = urllib.request.Request(
        OLLAMA_CHAT_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=180) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    return ((body.get("message") or {}).get("content") or "").strip()


def openai_chat(messages, api_key):
    payload = {
        "model": ONLINE_MODEL,
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + messages,
        "temperature": 0.7,
        "max_tokens": 384,
    }
    request = urllib.request.Request(
        OPENAI_CHAT_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + api_key,
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=60) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    return (body["choices"][0]["message"]["content"] or "").strip()


class FuryuApp:
    def __init__(self):
        self.messages = []
        self.busy = False
        self.local_ready = False

        GLib.set_prgname("furyu")
        GLib.set_application_name("Furyu")

        self.window = Gtk.Window(title="Furyu")
        self.window.set_default_size(780, 640)
        self.window.set_border_width(12)
        self.window.connect("destroy", self.on_destroy)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.window.add(root)

        title = Gtk.Label()
        title.set_markup("<span size='x-large' weight='bold'>Furyu</span>")
        title.set_xalign(0)

        self.welcome = Gtk.Label(label=WELCOME)
        self.welcome.set_xalign(0)
        self.welcome.set_line_wrap(True)
        self.welcome.set_max_width_chars(72)
        self.welcome.set_selectable(True)

        mode_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        mode_label = Gtk.Label(label="Modo")
        mode_label.set_xalign(0)
        self.local_radio = Gtk.RadioButton.new_with_label_from_widget(
            None, "Local (Ollama)"
        )
        self.online_radio = Gtk.RadioButton.new_with_label_from_widget(
            self.local_radio, "Online"
        )
        self.local_radio.connect("toggled", self.on_mode)
        self.online_radio.connect("toggled", self.on_mode)
        mode_row.pack_start(mode_label, False, False, 0)
        mode_row.pack_start(self.local_radio, False, False, 0)
        mode_row.pack_start(self.online_radio, False, False, 0)

        key_label = Gtk.Label(label="Chave de API")
        key_label.set_xalign(0)
        self.key_entry = Gtk.Entry()
        self.key_entry.set_visibility(False)
        self.key_entry.set_placeholder_text("Não é usada no modo local")
        self.key_entry.set_hexpand(True)
        self.key_entry.set_sensitive(False)

        hist_label = Gtk.Label(label="Histórico")
        hist_label.set_xalign(0)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)
        self.history = Gtk.TextView()
        self.history.set_editable(False)
        self.history.set_cursor_visible(False)
        self.history.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.history.set_left_margin(10)
        self.history.set_right_margin(10)
        self.history.set_top_margin(8)
        self.history.set_bottom_margin(8)
        scrolled.add(self.history)
        self.buffer = self.history.get_buffer()
        self.end_mark = self.buffer.create_mark(
            "end", self.buffer.get_end_iter(), False
        )

        msg_label = Gtk.Label(label="Mensagem")
        msg_label.set_xalign(0)

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.entry = Gtk.Entry()
        self.entry.set_placeholder_text("Escreva em português")
        self.entry.set_hexpand(True)
        self.entry.connect("activate", self.on_send)
        self.button = Gtk.Button(label="Enviar")
        self.button.connect("clicked", self.on_send)
        row.pack_start(self.entry, True, True, 0)
        row.pack_start(self.button, False, False, 0)

        self.status = Gtk.Label(label="Verificando o Ollama…")
        self.status.set_xalign(0)
        self.status.set_line_wrap(True)
        self.status.set_max_width_chars(72)

        root.pack_start(self.build_menu(), False, False, 0)
        root.pack_start(title, False, False, 0)
        root.pack_start(self.welcome, False, False, 0)
        root.pack_start(mode_row, False, False, 0)
        root.pack_start(key_label, False, False, 0)
        root.pack_start(self.key_entry, False, False, 0)
        root.pack_start(hist_label, False, False, 0)
        root.pack_start(scrolled, True, True, 0)
        root.pack_start(msg_label, False, False, 0)
        root.pack_start(row, False, False, 0)
        root.pack_start(self.status, False, False, 0)

        self.window.show_all()
        GLib.idle_add(self.start_loading)

    def build_menu(self):
        menubar = Gtk.MenuBar()

        arquivo = Gtk.MenuItem(label="Arquivo")
        menu_arquivo = Gtk.Menu()
        sair = Gtk.MenuItem(label="Sair")
        sair.connect("activate", lambda *_args: self.window.destroy())
        menu_arquivo.append(sair)
        arquivo.set_submenu(menu_arquivo)
        menubar.append(arquivo)

        ajuda = Gtk.MenuItem(label="Ajuda")
        menu_ajuda = Gtk.Menu()
        sobre = Gtk.MenuItem(label="Sobre")
        sobre.connect("activate", self.on_about)
        menu_ajuda.append(sobre)
        ajuda.set_submenu(menu_ajuda)
        menubar.append(ajuda)

        return menubar

    def on_about(self, *_args):
        dialog = Gtk.MessageDialog(
            parent=self.window,
            modal=True,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.NONE,
            text="Sobre o Furyu",
        )
        dialog.format_secondary_text(
            "Furyu 0.1.0. Janela de conversa em português do Brasil. "
            "O modo local usa o Ollama neste computador, sem conta e sem "
            "telemetria. O modo online é opcional. Esta versão não é o "
            "editor completo e não traz o agente de código."
        )
        dialog.add_button("Fechar", Gtk.ResponseType.CLOSE)
        dialog.connect("response", lambda d, _r: d.destroy())
        dialog.present()

    def set_status(self, text):
        self.status.set_text(text)

    def append_history(self, who, text):
        end = self.buffer.get_end_iter()
        if self.buffer.get_char_count():
            self.buffer.insert(end, "\n\n")
            end = self.buffer.get_end_iter()
        self.buffer.insert(end, who + "\n")
        end = self.buffer.get_end_iter()
        self.buffer.insert(end, text.strip() + "\n")
        self.history.scroll_mark_onscreen(self.end_mark)

    def start_loading(self):
        threading.Thread(target=self.refresh_local, daemon=True).start()
        return False

    def refresh_local(self):
        ready = ollama_has_model()
        ui(lambda found=ready: self.apply_local_status(found))

    def apply_local_status(self, ready):
        self.local_ready = ready
        if self.busy or self.online_radio.get_active():
            return
        if ready:
            self.set_status(
                "Modo local pronto. Escreva em português e clique em Enviar."
            )
        else:
            self.set_status(MSG_MODELO_AUSENTE)

    def on_mode(self, button):
        if not button.get_active():
            return
        online = self.online_radio.get_active()
        self.key_entry.set_sensitive(online)
        if self.busy:
            return
        if online:
            self.set_status(
                "Modo online. A chave de API só é usada quando você clicar em Enviar."
            )
            return
        self.set_status("Verificando o Ollama…")
        threading.Thread(target=self.refresh_local, daemon=True).start()

    def on_send(self, *_args):
        text = self.entry.get_text().strip()
        if not text or self.busy:
            return
        online = self.online_radio.get_active()
        api_key = self.key_entry.get_text().strip() if online else ""
        if online and not api_key:
            self.set_status("Informe a chave de API para usar o modo online.")
            return
        self.busy = True
        self.button.set_sensitive(False)
        self.entry.set_text("")
        self.append_history("Você", text)
        self.messages.append({"role": "user", "content": text})
        if online:
            self.set_status("Gerando a resposta no modo online…")
            threading.Thread(
                target=self.ask_online,
                args=(list(self.messages), api_key),
                daemon=True,
            ).start()
        else:
            self.set_status("Consultando o Ollama…")
            threading.Thread(
                target=self.ask_ollama,
                args=(list(self.messages),),
                daemon=True,
            ).start()

    def ask_ollama(self, messages):
        if not ollama_has_model():
            ui(self.show_local_missing)
            return
        ui(lambda: self.set_status("Gerando a resposta no Ollama…"))
        try:
            answer = ollama_chat(messages)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                ui(self.show_local_missing)
            else:
                ui(lambda: self.show_error("Não foi possível obter a resposta do Ollama."))
            return
        except Exception:
            ui(self.show_local_missing)
            return
        if not answer:
            answer = "(O modelo não devolveu texto.)"
        ui(lambda text=answer: self.show_answer(text))

    def ask_online(self, messages, api_key):
        try:
            answer = openai_chat(messages, api_key)
        except urllib.error.HTTPError as exc:
            if exc.code in (401, 403):
                detail = "A chave de API foi recusada."
            else:
                detail = (
                    "Não foi possível usar o modo online. "
                    "Verifique a chave de API e a conexão."
                )
            ui(lambda text=detail: self.show_error(text))
            return
        except Exception:
            ui(
                lambda: self.show_error(
                    "Não foi possível usar o modo online. "
                    "Verifique a chave de API e a conexão."
                )
            )
            return
        if not answer:
            answer = "(O modelo não devolveu texto.)"
        ui(lambda text=answer: self.show_answer(text))

    def show_answer(self, answer):
        self.messages.append({"role": "assistant", "content": answer})
        self.append_history("Furyu", answer)
        self.busy = False
        self.button.set_sensitive(True)
        self.entry.grab_focus()
        if self.online_radio.get_active():
            self.set_status("Modo online. Escreva outra mensagem e clique em Enviar.")
        else:
            self.set_status("Modo local. Escreva outra mensagem e clique em Enviar.")

    def show_local_missing(self):
        self.local_ready = False
        self.busy = False
        self.button.set_sensitive(True)
        self.append_history("Furyu", MSG_MODELO_AUSENTE)
        self.set_status(MSG_MODELO_AUSENTE)
        self.entry.grab_focus()

    def show_error(self, detail):
        self.busy = False
        self.button.set_sensitive(True)
        self.append_history("Furyu", detail)
        self.set_status(detail)
        self.entry.grab_focus()

    def on_destroy(self, *_args):
        Gtk.main_quit()


def main():
    FuryuApp()
    Gtk.main()


if __name__ == "__main__":
    main()
