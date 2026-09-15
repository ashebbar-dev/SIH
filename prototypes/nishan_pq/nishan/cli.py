from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import ledger, pqc, watermark, witness
from .core import _require_healthy_signed_history, decrypt_and_attribute, encrypt_once, trace_leak
from .demo import run as run_demo
from .identity import create_identity
from .util import write_private


def _path(value: str) -> Path:
    return Path(value).expanduser().resolve()


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="nishan", description="NISHAN-PQ offline prototype")
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor", help="verify real post-quantum algorithm support")

    demo = commands.add_parser("demo", help="run the complete evidence-generating scenario")
    demo.add_argument("--work-dir", type=_path, default=_path("demo-run"))
    demo.add_argument("--null-samples", type=int, default=400)

    identity = commands.add_parser("create-identity")
    identity.add_argument("--root", type=_path, required=True)
    identity.add_argument("--id", required=True)
    identity.add_argument("--name", required=True)

    init_ledger = commands.add_parser("init-ledger")
    init_ledger.add_argument("--root", type=_path, required=True)
    init_ledger.add_argument("--identities", type=_path, required=True)
    init_ledger.add_argument("--validators", type=int, default=4)
    init_ledger.add_argument("--quorum", type=int, default=3)

    encrypt = commands.add_parser("encrypt")
    encrypt.add_argument("--source", type=_path, required=True)
    encrypt.add_argument("--identities", type=_path, required=True)
    encrypt.add_argument("--recipient", action="append", required=True)
    encrypt.add_argument("--output", type=_path, required=True)

    decrypt = commands.add_parser("decrypt")
    decrypt.add_argument("--package", type=_path, required=True)
    decrypt.add_argument("--identities", type=_path, required=True)
    decrypt.add_argument("--recipient", required=True)
    decrypt.add_argument("--authority-secret", type=_path, required=True)
    decrypt.add_argument("--ledger", type=_path, required=True)
    decrypt.add_argument("--output", type=_path, required=True)
    decrypt.add_argument("--witness-root", type=_path)
    decrypt.add_argument("--witness-public-key-sha3-256")

    trace = commands.add_parser("trace")
    trace.add_argument("--reference", type=_path, required=True)
    trace.add_argument("--suspect", type=_path, required=True)
    trace.add_argument("--authority-secret", type=_path, required=True)
    trace.add_argument("--ledger", type=_path, required=True)
    trace.add_argument("--evidence", type=_path)
    trace.add_argument("--null-samples", type=int, default=400)
    trace.add_argument("--familywise-alpha", type=float, default=0.01)
    trace.add_argument("--witness-root", type=_path)
    trace.add_argument("--witness-public-key-sha3-256")

    audit = commands.add_parser("audit-ledger")
    audit.add_argument("--root", type=_path, required=True)

    init_witness = commands.add_parser(
        "init-witness", help="create a separately administered PQ ledger-head witness"
    )
    init_witness.add_argument("--root", type=_path, required=True)

    checkpoint_witness = commands.add_parser(
        "checkpoint-witness", help="sign the current canonical ledger head"
    )
    checkpoint_witness.add_argument("--root", type=_path, required=True)
    checkpoint_witness.add_argument("--ledger", type=_path, required=True)

    audit_witness = commands.add_parser(
        "audit-witness", help="compare the ledger with the latest external checkpoint"
    )
    audit_witness.add_argument("--root", type=_path, required=True)
    audit_witness.add_argument("--ledger", type=_path, required=True)
    return root


def main(argv: list[str] | None = None) -> None:
    arguments = parser().parse_args(argv)
    if arguments.command == "doctor":
        result = pqc.support()
        payload = {**result.__dict__, "ready": result.ready}
    elif arguments.command == "demo":
        payload = run_demo(arguments.work_dir, null_samples=arguments.null_samples)
    elif arguments.command == "create-identity":
        payload = create_identity(arguments.root, arguments.id, arguments.name)
    elif arguments.command == "init-ledger":
        payload = ledger.initialize(
            arguments.root,
            arguments.validators,
            arguments.quorum,
            arguments.identities,
        )
    elif arguments.command == "encrypt":
        payload = encrypt_once(
            arguments.source, arguments.identities, arguments.recipient, arguments.output
        )
    elif arguments.command == "decrypt":
        payload = decrypt_and_attribute(
            arguments.package,
            arguments.identities,
            arguments.recipient,
            arguments.authority_secret,
            arguments.ledger,
            arguments.output,
            witness_root=arguments.witness_root,
            witness_public_key_sha3_256=arguments.witness_public_key_sha3_256,
        )
    elif arguments.command == "trace":
        payload = trace_leak(
            arguments.reference,
            arguments.suspect,
            arguments.authority_secret,
            arguments.ledger,
            arguments.evidence,
            null_samples=arguments.null_samples,
            familywise_alpha=arguments.familywise_alpha,
            witness_root=arguments.witness_root,
            witness_public_key_sha3_256=arguments.witness_public_key_sha3_256,
        )
    elif arguments.command == "audit-ledger":
        payload = ledger.audit(arguments.root)
    elif arguments.command == "init-witness":
        payload = witness.initialize(arguments.root)
    elif arguments.command == "checkpoint-witness":
        if arguments.root.resolve() == arguments.ledger.resolve():
            raise ValueError("witness root must differ from ledger root")
        with ledger.exclusive(arguments.ledger):
            with witness.exclusive(arguments.root):
                payload = witness.checkpoint(arguments.root,
                    _require_healthy_signed_history(arguments.ledger), lock_held=True)
    elif arguments.command == "audit-witness":
        payload = witness.audit(
            arguments.root, ledger.audit(arguments.ledger)
        )
    else:  # pragma: no cover
        raise AssertionError(arguments.command)
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
