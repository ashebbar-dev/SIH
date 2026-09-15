"""Fresh public synthetic safeguard scenarios; real PQC is mandatory.

Run from the workspace with its prepared .venv. Existing populated output roots
are rejected. This is a protocol demonstration, not a population benchmark.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import multiprocessing as mp
import os
import queue
import shutil
import sys
import traceback
from dataclasses import asdict
from pathlib import Path
from unittest.mock import patch

import pymupdf as fitz

from nishan import core, ledger, pqc, witness
from nishan.demo import _sample_pdf, _transplant_first_image
from nishan.identity import create_identity
from nishan.util import sha3_file, write_json, write_private


def _release_worker(root_string, recipient, pin, barrier, results):
    root = Path(root_string)
    try:
        barrier.wait(timeout=120)
        result = core.decrypt_and_attribute(root / "package.json", root / "identities",
            recipient, root / "secret.bin", root / "ledger", root / f"{recipient}.pdf",
            witness_root=root / "witness", witness_public_key_sha3_256=pin)
        results.put({"result": result})
    except BaseException:
        results.put({"error": traceback.format_exc()})


def _concurrent(root, pin):
    context = mp.get_context("spawn")
    barrier, results = context.Barrier(2), context.Queue()
    workers = [context.Process(target=_release_worker,
        args=(str(root), name, pin, barrier, results)) for name in ("alice", "bob")]
    try:
        for worker in workers:
            worker.start()
        outputs = []
        for _ in workers:
            try:
                item = results.get(timeout=180)
            except queue.Empty as error:
                raise RuntimeError("concurrent worker timeout") from error
            if "error" in item:
                raise RuntimeError(item["error"])
            outputs.append(item["result"])
        for worker in workers:
            worker.join(20)
            if worker.is_alive() or worker.exitcode != 0:
                raise RuntimeError(f"concurrent worker exit: {worker.exitcode}")
        return sorted(outputs, key=lambda item: item["event"]["recipient_id"])
    finally:
        for worker in workers:
            if worker.is_alive():
                worker.terminate()
            worker.join(5)
        results.close()


def _rejection(action):
    try:
        action()
    except RuntimeError as error:
        return {"rejected": True, "error_type": type(error).__name__, "error": str(error)}
    return {"rejected": False}


def run(output: Path) -> dict:
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"refusing populated output root: {output}")
    output.mkdir(parents=True, exist_ok=True)
    workspace = Path(__file__).resolve().parents[3]
    source_files = sorted((workspace / "prototypes/nishan_pq/nishan").glob("*.py"))
    source_files += [Path(__file__).resolve(),
        workspace / "prototypes/nishan_pq/tests/test_release_safeguards.py",
        workspace / "prototypes/nishan_pq/tests/test_pdf_format_policy.py"]
    readiness = pqc.support()
    report = {
        "version": "nishan-selection-safeguards/v1",
        "command": ".venv/bin/python prototypes/nishan_pq/tools/demo_release_safeguards.py --output " + str(output),
        "pqc_ready": bool(readiness.ready),
        "pqc_profile": asdict(readiness),
        "profile": {"fixture": "nishan.demo._sample_pdf; public synthetic one-page PDF",
            "roster_size": core.TARDOS_ROSTER_SIZE, "coalition_limit": core.TARDOS_COALITION_LIMIT,
            "familywise_epsilon": core.TARDOS_FAMILYWISE_EPSILON,
            "fusion_policy": "pdf-all-formats-corroboration/v1",
            "pin_provisioning": "fresh local witness initialization in this demo; independent provisioning remains a deployment requirement"},
        "cases": [], "all_passed": False,
        "code_sha256": {str(path.relative_to(workspace)): hashlib.sha256(path.read_bytes()).hexdigest()
                        for path in source_files},
        "limitations": [
            "Scenario checks on public synthetic fixtures, not independent population trials or production certification.",
            "Witness and validator administration and private keys are co-located; no hardware isolation or independent-admin claim.",
            "Pinned state detects ledger rollback only while the provisioned key and retained witness state remain trustworthy; rollback of the witness too is outside this local guarantee.",
            "The authority can reproduce carriers and frame a session; software/key custody is trusted. A release session is not proof of human guilt, delivery or reading.",
            "Tracing is non-blind. Removal/retyping can defeat both carriers; raster and low-capacity PDF leads never become corroborated attribution.",
            "Historical JPEG-Q55 30/30 was a visual-channel experiment on one document/codebook with repeated sessions, not this strict verdict or physical performance.",
            "Historical shipped physical threshold recovered 0/4; experimental profiles recovered the same 1/4 capture.",
            "A committed authorization survives checkpoint/publication failure; explicit review and checkpoint recovery are required.",
            "Fresh keys and secrets are synthetic demo-only material and must not be reused for real documents.",
        ],
    }

    def case(name, passed, observed):
        report["cases"].append({"name": name, "passed": bool(passed), "observed": observed})

    try:
        if not readiness.ready:
            raise RuntimeError("real PQC is unavailable; not a pass")
        root = output / "fixture"
        root.mkdir()
        source = root / "source.pdf"
        _sample_pdf(source)
        identities = root / "identities"
        for name in ("alice", "bob"):
            create_identity(identities, name, name.title())
        ledger_root = root / "ledger"
        ledger.initialize(ledger_root, validator_count=4, quorum=3, identities_root=identities)
        secret = root / "secret.bin"
        write_private(secret, os.urandom(32))
        package = root / "package.json"
        core.encrypt_once(source, identities, ["alice", "bob"], package)
        witness_root = root / "witness"
        pin = witness.initialize(witness_root)["public_key_sha3_256"]
        witness.checkpoint(witness_root, ledger.audit(ledger_root))
        strict = {"witness_root": witness_root, "witness_public_key_sha3_256": pin}
        copies = _concurrent(root, pin)
        rows = [item["event"]["fingerprint"]["user_index"] for item in copies]
        sessions = [item["event"]["session_id"] for item in copies]
        case("concurrent_distinct_sessions_rows", sorted(rows) == [0, 1] and len(set(sessions)) == 2,
             {"rows": rows, "sessions": sessions, "processes": 2, "barrier_before_decrypt": True})
        third = core.decrypt_and_attribute(package, identities, "alice", secret,
                                          ledger_root, root / "third.pdf", **strict)
        case("third_release_row", third["event"]["fingerprint"]["user_index"] == 2,
             {"row": third["event"]["fingerprint"]["user_index"], "session": third["event"]["session_id"]})
        copies.append(third)
        write_json(output / "release-results.json", copies)
        hashes = [{"session": item["event"]["session_id"],
                   "signed": item["event"]["released_copy_sha3_256"],
                   "actual": sha3_file(Path(item["output"]))} for item in copies]
        case("signed_copy_hash_match", all(item["signed"] == item["actual"] for item in hashes), hashes)
        before = (witness_root / "checkpoints.jsonl").read_bytes()
        with patch.object(witness, "checkpoint", side_effect=AssertionError("trace attempted checkpoint")):
            clean = core.trace_leak(source, root / "alice.pdf", secret, ledger_root,
                                   output / "clean-evidence.json", **strict)
        case("clean_pdf_trace", clean["channel_decision"]["decision"] == "corroborated_channels"
             and [row["session_id"] for row in clean["attribution"]] == [copies[0]["event"]["session_id"]],
             {"decision": clean["channel_decision"], "attribution": clean["attribution"],
              "ledger_witness": clean["ledger_witness"]})
        case("trace_read_only", before == (witness_root / "checkpoints.jsonl").read_bytes(),
             {"before_sha256": hashlib.sha256(before).hexdigest(),
              "after_sha256": hashlib.sha256((witness_root / "checkpoints.jsonl").read_bytes()).hexdigest()})
        transplant, raster = root / "transplant.pdf", root / "transplant.png"
        _transplant_first_image(root / "alice.pdf", root / "bob.pdf", transplant)
        with fitz.open(transplant) as document:
            document[0].get_pixmap(dpi=144).save(raster)
        rendered = core.trace_leak(source, raster, secret, ledger_root,
                                  output / "rendered-transplant-evidence.json", **strict)
        case("rendered_transplant_abstains", not rendered["attribution"]
             and bool(rendered["visual_only_research_leads"])
             and rendered["channel_decision"]["decision"] == "abstain_missing_layout_channel",
             {"decision": rendered["channel_decision"], "attribution": rendered["attribution"],
              "visual_only_research_leads": rendered["visual_only_research_leads"]})
        short, short_package, short_copy = root / "short.pdf", root / "short-package.json", root / "short-copy.pdf"
        with fitz.open() as document:
            page = document.new_page(width=595, height=842)
            page.insert_text((60, 90), "Short synthetic fixture")
            document.save(short, no_new_id=True, reproducible=True)
        core.encrypt_once(short, identities, ["alice"], short_package)
        low_release = core.decrypt_and_attribute(short_package, identities, "alice", secret,
                                                ledger_root, short_copy, **strict)
        low = core.trace_leak(short, short_copy, secret, ledger_root,
                             output / "low-capacity-evidence.json", **strict)
        case("low_capacity_pdf_abstains", not low["attribution"] and bool(low["visual_only_research_leads"])
             and low["channel_decision"]["decision"] == "abstain_inadequate_release_capacity"
             and not low_release["event"]["fingerprint"]["layout_tag"]["available"],
             {"decision": low["channel_decision"], "attribution": low["attribution"],
              "signed_fingerprint_policy": low_release["event"]["fingerprint"],
              "visual_only_research_leads": low["visual_only_research_leads"]})
        wrong_output = root / "wrong-pin.pdf"
        wrong = _rejection(lambda: core.decrypt_and_attribute(package, identities, "alice", secret,
            ledger_root, wrong_output, **{**strict, "witness_public_key_sha3_256": "0" * 64}))
        wrong["output_exists"] = wrong_output.exists()
        case("wrong_pin_rejected", wrong["rejected"] and not wrong["output_exists"], wrong)
        rollback = output / "rollback-ledger"
        shutil.copytree(ledger_root, rollback)
        for replica in (rollback / "replicas").glob("*/ledger.jsonl"):
            lines = replica.read_bytes().splitlines(keepends=True)
            replica.write_bytes(b"".join(lines[:-1]))
        rollback_state = ledger.audit(rollback)
        rollback_output = root / "rollback.pdf"
        rejected = _rejection(lambda: core.decrypt_and_attribute(package, identities, "alice", secret,
                                rollback, rollback_output, **strict))
        rejected.update({"output_exists": rollback_output.exists(), "ledger_quorum_valid": rollback_state["quorum_valid"],
                         "comparison": witness.audit(witness_root, rollback_state)["ledger_comparison"]})
        case("rollback_release_rejected", rejected["rejected"] and not rejected["output_exists"]
             and rejected["ledger_quorum_valid"] and rejected["comparison"] == "rollback_detected", rejected)
        rejected = _rejection(lambda: core.trace_leak(source, root / "alice.pdf", secret, rollback, **strict))
        case("rollback_trace_rejected", rejected["rejected"], rejected)
        for existing in (False, True):
            failure_ledger, failure_witness = output / f"failure-{existing}-ledger", output / f"failure-{existing}-witness"
            shutil.copytree(ledger_root, failure_ledger)
            shutil.copytree(witness_root, failure_witness)
            destination = root / f"checkpoint-failure-{existing}.pdf"
            if existing:
                destination.write_bytes(b"existing destination")
            before_length = ledger.audit(failure_ledger)["canonical_length"]
            with patch.object(witness, "checkpoint", side_effect=RuntimeError("injected checkpoint failure")):
                rejected = _rejection(lambda: core.decrypt_and_attribute(package, identities, "alice", secret,
                    failure_ledger, destination, witness_root=failure_witness, witness_public_key_sha3_256=pin))
            after_state = ledger.audit(failure_ledger)
            preserved = destination.read_bytes() == b"existing destination" if destination.exists() and existing else not destination.exists() and not existing
            rejected.update({"existing_destination": existing, "destination_preserved": preserved,
                "before_length": before_length, "after_length": after_state["canonical_length"],
                "comparison": witness.audit(failure_witness, after_state)["ledger_comparison"]})
            case("checkpoint_failure_preserves_existing_output" if existing else "checkpoint_failure_no_publication",
                 rejected["rejected"] and preserved and after_state["canonical_length"] == before_length + 1
                 and rejected["comparison"] == "unwitnessed_extension", rejected)
    except Exception as error:
        case("harness_error", False, {"error": str(error), "traceback": traceback.format_exc()})
    report["all_passed"] = report["pqc_ready"] and len(report["cases"]) == 12 and all(case["passed"] for case in report["cases"])
    write_json(output / "results.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    result = run(arguments.output)
    print(json.dumps({"results": str(arguments.output / "results.json"), "pqc_ready": result["pqc_ready"],
                      "cases": len(result["cases"]), "all_passed": result["all_passed"]}, indent=2))
    return 0 if result["all_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
