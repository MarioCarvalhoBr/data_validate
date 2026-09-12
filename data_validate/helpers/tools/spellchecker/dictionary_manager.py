#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
from __future__ import annotations

import contextlib
import os
import tempfile
from pathlib import Path
from typing import Iterator, List

from enchant import Broker, Dict


class DictionaryManager:
    """Enchant dictionary manager for spell checking operations.

    Manages dictionary initialization and word loading. User-provided and
    extra words are added to the in-memory session word list only
    (`Dict.add_to_session`), never persisted to disk (BUG-022); the
    `ENCHANT_CONFIG_DIR` environment variable Enchant needs to locate the
    bundled hunspell dictionaries is scoped to a session-only temporary
    directory and restored to its previous value after each use, instead of
    being mutated for the whole process (SEC-007).

    Attributes:
        lang_dict_spell: Language code for the spell check dictionary
        dictionary: Enchant dictionary instance
        broker: Enchant broker instance
        path_dictionary: Path to the bundled dictionaries folder
    """

    def __init__(self, lang_dict_spell: str):
        """Initialize dictionary manager with specified language.

        Args:
            lang_dict_spell: Language code (e.g., 'pt_BR', 'en_US')
        """
        self.lang_dict_spell = lang_dict_spell
        self.dictionary: Dict | None = None
        self.broker: Broker | None = None
        self._errors: List[str] = []
        self.path_dictionary: Path = Path(__file__).resolve().parents[3] / "static" / "dictionaries"
        self._enchant_session_dir: tempfile.TemporaryDirectory | None = None

    def _ensure_enchant_session_dir(self) -> Path:
        """Create, once per manager, a session-scoped Enchant config directory.

        Enchant's hunspell backend offers no per-`Broker` way to point at the
        bundled dictionaries: `Broker.set_param` is documented as a no-op
        with the Enchant C library >= 2.0 (this project links 2.3.3), and
        every broker/dict call re-reads `ENCHANT_CONFIG_DIR` from the
        process environment rather than caching it on the `Broker` object.
        Pointing that variable directly at `static/dictionaries` (the
        pre-SEC-007 behaviour) also makes Enchant treat the package
        directory as the home for its auto-managed personal word list, so
        merely requesting a dictionary silently wrote `<lang>.dic` /
        `<lang>.exc` inside the installed package (BUG-022) even before any
        word was added.

        Instead, this creates a throwaway directory for the lifetime of this
        manager and symlinks the bundled `hunspell/` folder into it, so
        Enchant still finds the real dictionaries. Any file Enchant writes
        as a side effect of opening a dictionary lands in that temporary
        directory, which `clean_temporary_files` discards wholesale.

        Returns:
            Path: The session-scoped directory to use as `ENCHANT_CONFIG_DIR`.
        """
        if self._enchant_session_dir is None:
            self._enchant_session_dir = tempfile.TemporaryDirectory(prefix="canoa-enchant-")
            session_path = Path(self._enchant_session_dir.name)
            (session_path / "hunspell").symlink_to(self.path_dictionary / "hunspell", target_is_directory=True)

        return Path(self._enchant_session_dir.name)

    @contextlib.contextmanager
    def _enchant_config_dir_scope(self) -> Iterator[None]:
        """Temporarily point Enchant at the session-scoped dictionary directory.

        The previous value of `ENCHANT_CONFIG_DIR` (or its absence) is
        restored once the wrapped block finishes, so this manager never
        leaves the process environment mutated (SEC-007).
        """
        session_dir = self._ensure_enchant_session_dir()
        previous_value = os.environ.get("ENCHANT_CONFIG_DIR")
        os.environ["ENCHANT_CONFIG_DIR"] = str(session_dir)
        try:
            yield
        finally:
            if previous_value is None:
                os.environ.pop("ENCHANT_CONFIG_DIR", None)
            else:
                os.environ["ENCHANT_CONFIG_DIR"] = previous_value

    def validate_dictionary(self) -> List[str]:
        """Check if the specified dictionary exists.

        Returns:
            List of validation error messages, empty if valid
        """
        try:
            with self._enchant_config_dir_scope():
                self.broker = Broker()
                if not self.broker.dict_exists(self.lang_dict_spell):
                    self._errors.append(f"Dicionário {self.lang_dict_spell} não encontrado")
        except Exception as e:
            self._errors.append(f"Erro ao verificar dicionário: {e}")

        return self._errors

    def initialize_dictionary(self, list_words_user) -> Dict | None:
        """Initialize Enchant dictionary and load custom words.

        Loads extra words from extra-words.dic file and adds user-provided words.
        Words are added to the session-only word list (`Dict.add_to_session`)
        so nothing is persisted to disk (BUG-022).

        Args:
            list_words_user: List of custom words to add to dictionary

        Returns:
            Enchant dictionary instance or None if initialization failed
        """
        try:
            with self._enchant_config_dir_scope():
                if not self.broker:
                    self.broker = Broker()

                self.dictionary = self.broker.request_dict(self.lang_dict_spell)

                # Add extra words from extra-words.dic file
                self._load_extra_words()

                # Add user words
                for word in list_words_user:
                    if word and not word.startswith("#"):
                        self.dictionary.add_to_session(word)

            return self.dictionary
        except Exception as e:
            self._errors.append(f"Erro ao inicializar dicionário {self.lang_dict_spell}: {e}")

    def _load_extra_words(self) -> None:
        """Load additional words from extra-words.dic file.

        Reads the extra-words.dic file and adds each non-comment line
        to the dictionary's session-only word list. Ignores lines starting
        with '#'.
        """
        try:
            extra_words_path = self.path_dictionary / "extra-words.dic"

            if extra_words_path.exists():
                with open(extra_words_path, "r", encoding="utf-8") as file:
                    for line in file:
                        word = line.strip()
                        if word and not word.startswith("#"):  # Ignore empty lines and comments
                            self.dictionary.add_to_session(word)
            else:
                self._errors.append(
                    "Arquivo extra-words.dic não encontrado. Reporte o erro ao administrador do sistema."
                )

        except Exception as e:
            # Log the error but don't interrupt execution
            self._errors.append(f"Aviso: Não foi possível carregar palavras extras: {e}")

    def clean_temporary_files(self) -> None:
        """Release Enchant broker/dictionary references and the session directory.

        Historically this method also deleted `.dic`/`.exc` personal-dictionary
        files that Enchant wrote into the package's `static/dictionaries`
        directory (BUG-022). Since custom words are now added with
        `Dict.add_to_session` inside a session-scoped temporary directory
        (SEC-007), nothing is ever written under the package directory, so
        there is nothing to delete there; this method now only drops the
        broker/dictionary references and discards the temporary directory
        (if one was created) so the underlying resources can be released.
        """
        try:
            if self.dictionary:
                self.dictionary = None

            if self.broker:
                self.broker = None
        except Exception as e:
            self._errors.append(f"Warning: Could not cleanup Enchant resources: {e}")

        if self._enchant_session_dir is not None:
            self._enchant_session_dir.cleanup()
            self._enchant_session_dir = None
