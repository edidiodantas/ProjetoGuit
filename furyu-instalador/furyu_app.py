#!/usr/bin/env python3
"""Janela de teste do Furyu.

Conversa offline com o Amadeus Verbo. Não é o editor completo.
"""

import json
import os
import signal
import socket
import subprocess
import sys
import threading
import urllib.error
import urllib.request

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk

GGUF_NAME = "Amadeus-Verbo-FI-Qwen2.5-0.5B-PT-BR-Instruct.Q4_K_M.gguf"
SYSTEM_PROMPT = (
    "Você é o Furyu, um assistente de teste. "
    "Responda sempre em português do Brasil, de forma clara e curta."
)


def find_gguf():
    candidates = [
        os.path.join("/usr/share/furyu", GGUF_NAME),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), GGUF_NAME),
        os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), GGUF_NAME),
    ]
    seen = set()
    for path in candidates:
        if path in seen:
            continue
        seen.add(path)
        if os.path.isfile(path) and os.path.getsize(path) > 1_000_000:
            return path
    return None


def find_server():
    candidates = [
        "/usr/lib/furyu/llama-server",
        "/usr/local/bin/llama-server",
    ]
    for folder in os.environ.get("PATH", "").split(os.pathsep):
        if folder:
            candidates.append(os.path.join(folder, "llama-server"))
    seen = set()
    for path in candidates:
        if path in seen:
            continue
        seen.add(path)
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    return None


def free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def ui(callback):
    def wrapper():
        callback()
        return False

    GLib.idle_add(wrapper)


class FuryuApp:
    def __init__(self):
        self.messages = []
        self.proc = None
        self.port = None
        self.ready = False
        self.busy = False
        self.model = find_gguf()
        self.server = find_server()
        self.log_path = os.path.join(
            os.path.expanduser("~"), ".cache", "furyu", "llama-server.log"
        )

        self.window = Gtk.Window(title="Furyu")
        self.window.set_default_size(760, 560)
        self.window.set_border_width(12)
        self.window.connect("destroy", self.on_destroy)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.window.add(root)

        title = Gtk.Label()
        title.set_markup("<span size='x-large' weight='bold'>Furyu</span>")
        title.set_xalign(0)
        subtitle = Gtk.Label(
            label=(
                "Teste em português com o Amadeus Verbo, na CPU. "
                "Esta janela não é o editor completo."
            )
        )
        subtitle.set_xalign(0)
        subtitle.set_line_wrap(True)
        subtitle.set_max_width_chars(70)

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
        self.end_mark = self.buffer.create_mark("end", self.buffer.get_end_iter(), False)

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

        self.status = Gtk.Label(label="Abrindo…")
        self.status.set_xalign(0)
        self.status.set_line_wrap(True)

        root.pack_start(title, False, False, 0)
        root.pack_start(subtitle, False, False, 0)
        root.pack_start(hist_label, False, False, 0)
        root.pack_start(scrolled, True, True, 0)
        root.pack_start(msg_label, False, False, 0)
        root.pack_start(row, False, False, 0)
        root.pack_start(self.status, False, False, 0)

        self.window.show_all()
        GLib.idle_add(self.start_loading)

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
        if not self.model:
            self.button.set_sensitive(False)
            self.set_status(
                "Falta o arquivo "
                + GGUF_NAME
                + " em /usr/share/furyu/ ou ao lado do programa."
            )
            return False
        if not self.server:
            self.button.set_sensitive(False)
            self.set_status(
                "Falta o llama-server. Rode bash instalar-linux.sh na pasta do pendrive."
            )
            return False
        self.button.set_sensitive(False)
        self.set_status("Carregando o modelo na CPU. No i5 de 3ª geração isso pode levar um minuto.")
        threading.Thread(target=self.boot_server, daemon=True).start()
        return False

    def boot_server(self):
        try:
            self.port = free_port()
            os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
            log = open(self.log_path, "wb")
            cmd = [
                self.server,
                "-m",
                self.model,
                "-c",
                "2048",
                "-t",
                "4",
                "-ngl",
                "0",
                "-fa",
                "off",
                "--fit",
                "off",
                "--cache-ram",
                "256",
                "--no-warmup",
                "--reasoning",
                "off",
                "--host",
                "127.0.0.1",
                "--port",
                str(self.port),
            ]
            self.proc = subprocess.Popen(
                cmd,
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            if not self.wait_ready(180):
                detail = self.failure_text()
                ui(lambda: self.fail_boot(detail))
                return
            ui(self.mark_ready)
        except Exception as exc:
            ui(lambda: self.fail_boot(str(exc)))

    def wait_ready(self, timeout):
        import time

        deadline = time.time() + timeout
        url = "http://127.0.0.1:%d/health" % self.port
        while time.time() < deadline:
            if self.proc.poll() is not None:
                return False
            try:
                with urllib.request.urlopen(url, timeout=2) as resp:
                    if resp.status == 200:
                        return True
            except urllib.error.HTTPError as exc:
                if exc.code == 200:
                    return True
            except Exception:
                pass
            time.sleep(0.4)
        return False

    def failure_text(self):
        code = self.proc.returncode if self.proc else None
        tail = ""
        try:
            with open(self.log_path, "r", encoding="utf-8", errors="replace") as handle:
                lines = handle.read().splitlines()
            tail = " ".join(lines[-8:])
        except OSError:
            tail = ""
        if code in (132, -signal.SIGILL) or "Illegal instruction" in tail:
            return (
                "O llama-server parou com instrução ilegal. "
                "Este PC precisa do llama.cpp compilado com AVX, sem AVX2. "
                "Rode bash instalar-linux.sh de novo."
            )
        if tail:
            return "Não foi possível carregar o modelo. " + tail[-400:]
        return "Não foi possível carregar o modelo. Veja " + self.log_path

    def fail_boot(self, detail):
        self.ready = False
        self.button.set_sensitive(False)
        self.set_status(detail)

    def mark_ready(self):
        self.ready = True
        self.button.set_sensitive(True)
        self.entry.grab_focus()
        self.set_status("Modelo pronto. Escreva em português e clique em Enviar.")

    def on_send(self, *_args):
        text = self.entry.get_text().strip()
        if not text or self.busy or not self.ready:
            return
        self.busy = True
        self.button.set_sensitive(False)
        self.entry.set_text("")
        self.append_history("Você", text)
        self.messages.append({"role": "user", "content": text})
        self.set_status("Gerando a resposta na CPU…")
        threading.Thread(target=self.ask, args=(list(self.messages),), daemon=True).start()

    def ask(self, messages):
        payload = {
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + messages,
            "temperature": 0.7,
            "max_tokens": 384,
            "stream": False,
        }
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            "http://127.0.0.1:%d/v1/chat/completions" % self.port,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=180) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            answer = body["choices"][0]["message"]["content"].strip()
            if not answer:
                answer = "(O modelo não devolveu texto.)"
            ui(lambda: self.show_answer(answer))
        except Exception as exc:
            ui(lambda: self.show_error(str(exc)))

    def show_answer(self, answer):
        self.messages.append({"role": "assistant", "content": answer})
        self.append_history("Furyu", answer)
        self.busy = False
        self.button.set_sensitive(True)
        self.entry.grab_focus()
        self.set_status("Escreva outra mensagem e clique em Enviar.")

    def show_error(self, detail):
        self.busy = False
        self.button.set_sensitive(self.ready)
        self.append_history("Furyu", "Não consegui responder agora.")
        self.set_status(detail[:400])

    def on_destroy(self, *_args):
        proc = self.proc
        if proc and proc.poll() is None:
            try:
                os.killpg(proc.pid, signal.SIGTERM)
            except OSError:
                proc.terminate()
        Gtk.main_quit()


def main():
    FuryuApp()
    Gtk.main()


if __name__ == "__main__":
    main()
