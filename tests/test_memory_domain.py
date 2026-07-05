"""
Tests for Memory Functional Yield domain (v2.3.0)
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

MEMORY_SAMPLE_DIR = Path(__file__).parent.parent / "samples" / "memory_device"


class TestSyntheticGenerator:
    def test_generates_block_health_csv_and_device_info(self):
        from yieldos.domains.memory.synthetic_gen import generate_all
        with tempfile.TemporaryDirectory() as tmpdir:
            info = generate_all(tmpdir, n_blocks=64)
            assert Path(info["block_health_csv"]).exists()
            assert Path(info["device_info_json"]).exists()

    def test_generated_block_count(self):
        from yieldos.domains.memory.synthetic_gen import generate_all
        with tempfile.TemporaryDirectory() as tmpdir:
            import csv
            info = generate_all(tmpdir, n_blocks=64)
            with open(info["block_health_csv"], encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            assert len(rows) == 64

    def test_generated_csv_has_required_columns(self):
        from yieldos.domains.memory.synthetic_gen import generate_all
        with tempfile.TemporaryDirectory() as tmpdir:
            import csv
            info = generate_all(tmpdir, n_blocks=32)
            with open(info["block_health_csv"], encoding="utf-8") as f:
                reader = csv.DictReader(f)
                cols = reader.fieldnames or []
            for col in ["block_id", "block_size_gb", "is_factory_bad", "is_runtime_bad",
                        "corrected_error_count", "uncorrectable_error_count"]:
                assert col in cols, f"Missing required column: {col}"


class TestMemoryAnalyzerDomain:
    def test_domain_is_memory(self):
        from yieldos.domains.memory import MemoryAnalyzer
        with tempfile.TemporaryDirectory() as tmpdir:
            from yieldos.domains.memory.synthetic_gen import generate_all
            generate_all(tmpdir, n_blocks=64)
            result = MemoryAnalyzer().analyze(tmpdir)
            assert result["domain"] == "memory"

    def test_functional_capacity_has_required_fields(self):
        from yieldos.domains.memory import MemoryAnalyzer
        with tempfile.TemporaryDirectory() as tmpdir:
            from yieldos.domains.memory.synthetic_gen import generate_all
            generate_all(tmpdir, n_blocks=64)
            result = MemoryAnalyzer().analyze(tmpdir)
            fc = result["functional_capacity"]
            for key in ["raw_capacity_gb", "safe_capacity_gb", "approximate_cache_capacity_gb",
                        "read_only_archive_capacity_gb", "discarded_capacity_gb", "functional_yield"]:
                assert key in fc, f"Missing field: {key}"

    def test_capacities_sum_to_raw(self):
        from yieldos.domains.memory import MemoryAnalyzer
        with tempfile.TemporaryDirectory() as tmpdir:
            from yieldos.domains.memory.synthetic_gen import generate_all
            generate_all(tmpdir, n_blocks=64)
            result = MemoryAnalyzer().analyze(tmpdir)
            fc = result["functional_capacity"]
            total = (fc["safe_capacity_gb"] + fc["approximate_cache_capacity_gb"]
                     + fc["read_only_archive_capacity_gb"] + fc["discarded_capacity_gb"])
            assert abs(total - fc["raw_capacity_gb"]) < 0.01

    def test_functional_yield_is_0_to_1(self):
        from yieldos.domains.memory import MemoryAnalyzer
        with tempfile.TemporaryDirectory() as tmpdir:
            from yieldos.domains.memory.synthetic_gen import generate_all
            generate_all(tmpdir, n_blocks=64)
            result = MemoryAnalyzer().analyze(tmpdir)
            fy = result["functional_capacity"]["functional_yield"]
            assert 0.0 <= fy <= 1.0

    def test_bad_blocks_reduce_functional_yield(self):
        import csv

        from yieldos.domains.memory import MemoryAnalyzer
        from yieldos.domains.memory.synthetic_gen import generate_all

        with tempfile.TemporaryDirectory() as tmpdir_few:
            generate_all(tmpdir_few, n_blocks=32, seed=42)
            result_few = MemoryAnalyzer().analyze(tmpdir_few)
            fy_few = result_few["functional_capacity"]["functional_yield"]

        with tempfile.TemporaryDirectory() as tmpdir_many:
            # Generate with forced factory-bad blocks by manipulating the CSV
            generate_all(tmpdir_many, n_blocks=32, seed=42)
            csv_path = Path(tmpdir_many) / "block_health.csv"
            rows = []
            with csv_path.open(encoding="utf-8") as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames
                for i, row in enumerate(reader):
                    if i < 16:  # mark first half as factory bad
                        row["is_factory_bad"] = "true"
                    rows.append(row)
            with csv_path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            result_many = MemoryAnalyzer().analyze(tmpdir_many)
            fy_many = result_many["functional_capacity"]["functional_yield"]

        assert fy_many < fy_few

    def test_uncorrectable_errors_produce_evidence_object(self):
        import csv

        from yieldos.domains.memory import MemoryAnalyzer
        from yieldos.domains.memory.synthetic_gen import generate_all

        with tempfile.TemporaryDirectory() as tmpdir:
            generate_all(tmpdir, n_blocks=32, seed=42)
            csv_path = Path(tmpdir) / "block_health.csv"
            rows = []
            with csv_path.open(encoding="utf-8") as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames
                for i, row in enumerate(reader):
                    if i == 0:
                        row["uncorrectable_error_count"] = "2"
                        row["is_factory_bad"] = "false"
                        row["is_runtime_bad"] = "false"
                    rows.append(row)
            with csv_path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            result = MemoryAnalyzer().analyze(tmpdir)
            pack = result["evidence_pack"]
            # evidence_objects are dicts after seal()
            ev_metrics = [
                e.get("metric", "") if isinstance(e, dict) else getattr(e, "metric", "")
                for e in pack.evidence_objects
            ]
            assert "uncorrectable_error_count" in ev_metrics

    def test_passport_roles_are_present(self):
        from yieldos.domains.memory import MemoryAnalyzer
        with tempfile.TemporaryDirectory() as tmpdir:
            from yieldos.domains.memory.synthetic_gen import generate_all
            generate_all(tmpdir, n_blocks=64)
            result = MemoryAnalyzer().analyze(tmpdir)
            assert len(result["remaining_roles"]) > 0
            assert isinstance(result["blocked_roles"], list)
            assert result["bin_class"]

    def test_recovery_candidates_no_hardware_execution(self):
        from yieldos.domains.memory import MemoryAnalyzer
        with tempfile.TemporaryDirectory() as tmpdir:
            from yieldos.domains.memory.synthetic_gen import generate_all
            generate_all(tmpdir, n_blocks=64)
            result = MemoryAnalyzer().analyze(tmpdir)
            for rc in result["recovery_candidates"]:
                assert not rc.hardware_execution_enabled


class TestMemoryCLI:
    def test_memory_analyze_creates_functional_capacity_json(self):
        from yieldos.cli.main import cmd_memory_analyze
        from yieldos.domains.memory.synthetic_gen import generate_all
        with tempfile.TemporaryDirectory() as inp_dir:
            generate_all(inp_dir, n_blocks=64)
            with tempfile.TemporaryDirectory() as out_dir:
                args = argparse.Namespace(
                    input=inp_dir, out=out_dir,
                    asset="test_memdev", case=None,
                )
                rc = cmd_memory_analyze(args)
                assert rc == 0
                assert (Path(out_dir) / "memory_functional_capacity.json").exists()

    def test_memory_validate_strict_passes(self):
        from yieldos.cli.main import cmd_memory_analyze, cmd_validate
        from yieldos.domains.memory.synthetic_gen import generate_all
        with tempfile.TemporaryDirectory() as inp_dir:
            generate_all(inp_dir, n_blocks=64)
            with tempfile.TemporaryDirectory() as out_dir:
                analyze_args = argparse.Namespace(
                    input=inp_dir, out=out_dir,
                    asset="test_memdev", case=None,
                )
                cmd_memory_analyze(analyze_args)
                val_args = argparse.Namespace(case=out_dir, strict=True)
                rc = cmd_validate(val_args)
                assert rc == 0

    def test_memory_outputs_in_case_manifest(self):
        from yieldos.cli.main import cmd_memory_analyze
        from yieldos.domains.memory.synthetic_gen import generate_all
        with tempfile.TemporaryDirectory() as inp_dir:
            generate_all(inp_dir, n_blocks=64)
            with tempfile.TemporaryDirectory() as out_dir:
                args = argparse.Namespace(
                    input=inp_dir, out=out_dir,
                    asset="test_memdev", case=None,
                )
                cmd_memory_analyze(args)
                manifest_path = Path(out_dir) / "case_manifest.json"
                assert manifest_path.exists()
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                files = manifest.get("files", {})
                assert any("memory_functional_capacity" in k for k in files)

    def test_sample_data_files_exist(self):
        assert (MEMORY_SAMPLE_DIR / "block_health.csv").exists()
        assert (MEMORY_SAMPLE_DIR / "device_info.json").exists()
        assert (MEMORY_SAMPLE_DIR / "README.md").exists()
