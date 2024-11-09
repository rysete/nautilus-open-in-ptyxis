#!/usr/bin/python3

import shutil
import subprocess
import logging
import os
from typing import List, Optional
from gettext import gettext as _
from pathlib import Path
from enum import Enum, auto
from dataclasses import dataclass

from gi import require_version
require_version("Nautilus", "4.0")
require_version("Gtk", "4.0")
from gi.repository import GObject, Nautilus

# Configurações
class Config:
    TERMINAL_NAME = "org.gnome.Ptyxis.Devel"
    DEBUG_ENV_VAR = "NAUTILUS_PTYXIS_DEBUG"
    NATIVE_EXECUTABLES = {
        "ptyxis-terminal": "/usr/bin/ptyxis-terminal",
        "ptyxis": "/usr/bin/ptyxis"
    }

class TerminalType(Enum):
    PTYXIS_TERMINAL = auto()
    PTYXIS = auto()
    FLATPAK = auto()

@dataclass
class TerminalCommand:
    executable: str
    args: List[str]

class PtyxisTerminalLauncher:
    """Gerenciador para lançamento do terminal Ptyxis"""
    
    def __init__(self):
        self.terminal_type = self._detect_terminal_type()

    def _detect_terminal_type(self) -> TerminalType:
        """Detecta qual tipo de instalação do Ptyxis está disponível"""
        for exec_name, path in Config.NATIVE_EXECUTABLES.items():
            if shutil.which(exec_name) == path:
                return (TerminalType.PTYXIS_TERMINAL 
                       if exec_name == "ptyxis-terminal" 
                       else TerminalType.PTYXIS)
        return TerminalType.FLATPAK

    def _build_command(self, path: str) -> TerminalCommand:
        """Constrói o comando para lançar o terminal baseado no tipo detectado"""
        if self.terminal_type == TerminalType.FLATPAK:
            return TerminalCommand(
                executable="/usr/bin/flatpak",
                args=["run", Config.TERMINAL_NAME, "--new-window", "-d", path]
            )
        
        executable = ("ptyxis-terminal" 
                     if self.terminal_type == TerminalType.PTYXIS_TERMINAL 
                     else "ptyxis")
        return TerminalCommand(
            executable=executable,
            args=["--new-window", "-d", path]
        )

    def launch(self, path: str) -> None:
        """Lança uma nova janela do terminal no diretório especificado"""
        try:
            cmd = self._build_command(path)
            full_command = [cmd.executable] + cmd.args
            
            logging.debug("Launching terminal with command: %s", full_command)
            subprocess.Popen(
                full_command,
                cwd=path,
                start_new_session=True,
                # Redireciona saída de erro para evitar mensagens no terminal
                stderr=subprocess.DEVNULL
            )
        except subprocess.SubprocessError as e:
            logging.error("Failed to launch terminal: %s", e)
            raise

class PtyxisNautilus(GObject.GObject, Nautilus.MenuProvider):
    """Extensão Nautilus para integração com o Ptyxis Terminal"""

    def __init__(self):
        super().__init__()
        self.is_select = False
        self.launcher = PtyxisTerminalLauncher()
        
        # Configura logging se variável de debug estiver ativa
        if os.environ.get(Config.DEBUG_ENV_VAR, "False").lower() == "true":
            logging.basicConfig(level=logging.DEBUG)

    def get_file_items(self, files: List[Nautilus.FileInfo]) -> List[Nautilus.MenuItem]:
        """Retorna itens de menu ao clicar em arquivos/pastas"""
        if not self._validate_file_selection(files):
            return []

        file_info = files[0]
        self.is_select = False

        if file_info.is_directory():
            self.is_select = True
            dir_path = self._get_path(file_info)
            logging.debug("Selected directory: %s", dir_path)
            return [self._create_menu_item(dir_path)]

        return []

    def get_background_items(self, directory: Nautilus.FileInfo) -> List[Nautilus.MenuItem]:
        """Retorna itens de menu ao clicar no fundo da janela"""
        # Evita problemas de concorrência quando um diretório está selecionado
        if self.is_select:
            self.is_select = False
            return []

        if directory.is_directory():
            dir_path = self._get_path(directory)
            logging.debug("Background directory: %s", dir_path)
            return [self._create_menu_item(dir_path)]

        return []

    def _create_menu_item(self, path: str) -> Nautilus.MenuItem:
        """Cria o item de menu 'Abrir no Ptyxis'"""
        item = Nautilus.MenuItem(
            name="PtyxisNautilus::open_in_ptyxis",
            label=_("Open in Ptyxis"),
            tip=_("Open this folder in Ptyxis Terminal"),
        )
        
        item.connect("activate", self._handle_menu_activate, path)
        logging.debug("Created menu item for path: %s", path)
        return item

    def _handle_menu_activate(self, item: Nautilus.MenuItem, path: str) -> None:
        """Manipulador do evento de ativação do menu"""
        try:
            self.launcher.launch(path)
        except Exception as e:
            logging.error("Failed to handle menu activation: %s", e)

    @staticmethod
    def _get_path(file_info: Nautilus.FileInfo) -> str:
        """Obtém o caminho absoluto de um FileInfo"""
        return file_info.get_location().get_path()

    @staticmethod
    def _validate_file_selection(files: List[Nautilus.FileInfo]) -> bool:
        """Valida se apenas um arquivo está selecionado"""
        return len(files) == 1
