"""Shared fixtures for ExoBrain v2 test suite.

All tests use temporary directories so no real data is touched.
The settings singleton is patched so that db_path and files_dir
point into pytest's tmp_path.
"""

import os
import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest

from src.core.bootstrap import BOOTSTRAP_IDS, bootstrap
from src.core.db import get_connection, init_db, run_migrations
from src.core.repository import LinkRepo, ObjectRepo, TagRepo


@pytest.fixture()
def tmp_data_dir(tmp_path):
    """Create a temporary data directory and patch EXOBRAIN_DATA_DIR."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    files_dir = data_dir / "files"
    files_dir.mkdir()
    return data_dir


@pytest.fixture()
def tmp_db_path(tmp_data_dir):
    """Return a path for a temporary database file."""
    return tmp_data_dir / "exobrain.db"


@pytest.fixture()
def _patched_settings(tmp_data_dir):
    """Patch the global settings so data_dir points to tmp_path.

    This fixture must be used by any test that imports settings
    (directly or transitively through repository/db modules).
    """
    from src.config import settings

    original_data_dir = settings.data_dir
    original_cache_dir = settings.cache_dir

    settings.data_dir = tmp_data_dir
    settings.cache_dir = tmp_data_dir / "cache"
    settings.cache_dir.mkdir(parents=True, exist_ok=True)

    yield settings

    settings.data_dir = original_data_dir
    settings.cache_dir = original_cache_dir


@pytest.fixture()
def db_conn(tmp_db_path, _patched_settings):
    """Create an initialized DB with all migrations applied.

    Returns an open sqlite3.Connection. Closed after the test.
    """
    conn = init_db(tmp_db_path)
    yield conn
    conn.close()


@pytest.fixture()
def bootstrapped_db(db_conn):
    """An initialized DB with bootstrap types and spaces created.

    Returns the same connection as db_conn, after bootstrap() has run.
    """
    bootstrap(db_conn)
    return db_conn


@pytest.fixture()
def sample_objects(bootstrapped_db):
    """Create a few test objects with tags and links.

    Returns a dict with keys: conn, obj_a, obj_b, obj_c
    (each being the full object dict from ObjectRepo.create).
    """
    conn = bootstrapped_db
    obj_repo = ObjectRepo(conn)
    tag_repo = TagRepo(conn)
    link_repo = LinkRepo(conn)

    doc_type_id = BOOTSTRAP_IDS["document"]
    note_type_id = BOOTSTRAP_IDS["note"]
    space_id = BOOTSTRAP_IDS["primitives"]

    obj_a = obj_repo.create(
        type_id=doc_type_id,
        space_id=space_id,
        title="Alpha Document",
        summary="First test document about quantum computing",
        content="Quantum computing leverages superposition and entanglement.",
    )
    obj_b = obj_repo.create(
        type_id=doc_type_id,
        space_id=space_id,
        title="Beta Document",
        summary="Second test document about machine learning",
        content="Machine learning uses statistical methods to find patterns.",
    )
    obj_c = obj_repo.create(
        type_id=note_type_id,
        space_id=space_id,
        title="Gamma Note",
        summary="A short observation",
        content="Noticed a connection between quantum and ML approaches.",
    )

    # Tags
    tag_repo.add(obj_a["id"], "quantum")
    tag_repo.add(obj_a["id"], "computing")
    tag_repo.add(obj_b["id"], "machine-learning")
    tag_repo.add(obj_b["id"], "computing")
    tag_repo.add(obj_c["id"], "observation")

    # Links
    link_repo.create(obj_a["id"], obj_b["id"], "related-to")
    link_repo.create(obj_c["id"], obj_a["id"], "references")

    return {
        "conn": conn,
        "obj_a": obj_a,
        "obj_b": obj_b,
        "obj_c": obj_c,
    }
