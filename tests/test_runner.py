"""Tests for reproducible inference runner."""
from pathlib import Path

import pytest

from nomenclador_conceptos_luis.runner import compute_file_hashes


class TestComputeFileHashes:
    """Tests for file hash computation."""

    def test_hash_existing_file(self, tmp_path: Path) -> None:
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world")
        hashes = compute_file_hashes([test_file])
        assert "test.txt" in hashes
        assert len(hashes["test.txt"]) == 64  # SHA-256 hex length

    def test_hash_nonexistent_file(self, tmp_path: Path) -> None:
        test_file = tmp_path / "nonexistent.txt"
        hashes = compute_file_hashes([test_file])
        assert "nonexistent.txt" not in hashes

    def test_deterministic(self, tmp_path: Path) -> None:
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world")
        hashes1 = compute_file_hashes([test_file])
        hashes2 = compute_file_hashes([test_file])
        assert hashes1 == hashes2

    def test_different_files_different_hashes(self, tmp_path: Path) -> None:
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("content A")
        file2.write_text("content B")
        hashes = compute_file_hashes([file1, file2])
        assert hashes["file1.txt"] != hashes["file2.txt"]
