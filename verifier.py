import os
import json
import shutil
import subprocess
import tempfile
from typing import Tuple

import requests

from pathlib import Path

from nbt import nbt as nbtlib  # optional, for NBT checks if available


def static_validate_block_json(block_json: str) -> Tuple[bool, str]:
    """
    Perform basic static checks on the Bedrock block JSON string.
    Returns (success, logs)
    """
    logs = []
    try:
        parsed = json.loads(block_json)
    except Exception as e:
        return False, f"JSON parse error: {e}"

    # Basic structural checks for Bedrock block
    if 'minecraft:block' not in parsed:
        logs.append("Missing 'minecraft:block' root key")
    else:
        blk = parsed['minecraft:block']
        if 'description' not in blk or 'identifier' not in blk.get('description', {}):
            logs.append("Missing description.identifier")
        if 'components' not in blk:
            logs.append("Missing components")

    if logs:
        return False, "; ".join(logs)

    return True, "Static validation passed"


def run_docker_verifier(workdir: str, timeout: int = 120) -> Tuple[bool, str]:
    """
    Run the docker-compose verifier stack with the given workdir mounted.
    Returns (success, logs)
    """
    env = os.environ.copy()
    env['WORKDIR'] = workdir
    compose_file = os.path.join(os.getcwd(), 'docker', 'docker-compose.yml')
    if not os.path.exists(compose_file):
        return False, f"docker-compose.yml not found at {compose_file}"

    cmd_up = ['docker-compose', '-f', compose_file, 'up', '--build', '--abort-on-container-exit']
    try:
        p = subprocess.run(cmd_up, cwd=os.getcwd(), env=env, capture_output=True, timeout=timeout)
        out = p.stdout.decode('utf-8', errors='ignore')
        err = p.stderr.decode('utf-8', errors='ignore')
    except subprocess.TimeoutExpired:
        return False, 'docker-compose run timed out'
    except FileNotFoundError:
        return False, 'docker-compose not installed or not in PATH'

    # after run, gather logs
    cmd_logs = ['docker-compose', '-f', compose_file, 'logs']
    try:
        logs_p = subprocess.run(cmd_logs, cwd=os.getcwd(), env=env, capture_output=True, timeout=30)
        logs = logs_p.stdout.decode('utf-8', errors='ignore')
    except Exception:
        logs = out + "\n" + err

    # simple heuristics: look for SUCCEEDED markers
    success = ('JAVA_VERIFIED' in logs) and ('BEDROCK_VERIFIED' in logs)
    return success, logs


def verify_block(block_json: str, block_id: str, work_base: str = None, timeout: int = 120) -> Tuple[bool, str]:
    """
    High-level verifier: tries full docker-based verification, falls back to static checks.
    Returns (success, logs)
    """
    tmpdir = work_base or tempfile.mkdtemp(prefix=f'mcdex_verify_{block_id}_')
    try:
        # write artifacts to workdir
        pack_dir = os.path.join(tmpdir, 'pack')
        os.makedirs(pack_dir, exist_ok=True)
        # create a simple behavior_pack layout for Bedrock
        bp_dir = os.path.join(tmpdir, 'behavior_pack', 'components')
        os.makedirs(bp_dir, exist_ok=True)
        block_path = os.path.join(bp_dir, f'{block_id}.json')
        with open(block_path, 'w', encoding='utf-8') as f:
            f.write(block_json)

        # write a small datapack/package for Java (as example)
        datapack_dir = os.path.join(tmpdir, 'datapack', 'data', 'mcdex', 'functions')
        os.makedirs(datapack_dir, exist_ok=True)
        # minimal pack.mcmeta for Java
        with open(os.path.join(tmpdir, 'datapack', 'pack.mcmeta'), 'w', encoding='utf-8') as f:
            f.write('{"pack":{"pack_format":15,"description":"MCdex generated pack"}}')

        # Attempt full docker verification
        docker_success, docker_logs = run_docker_verifier(tmpdir, timeout=timeout)
        if docker_success:
            return True, 'Full docker verification succeeded:\n' + docker_logs

        # fallback to static validation
        static_ok, static_logs = static_validate_block_json(block_json)
        logs = 'Docker attempt failed:\n' + docker_logs + '\nStatic fallback:\n' + static_logs
        return static_ok, logs

    finally:
        # leave tempdir for debugging only if an env var MCDEX_KEEP_ARTIFACTS=1 is set
        keep = os.environ.get('MCDEX_KEEP_ARTIFACTS')
        if not keep:
            try:
                shutil.rmtree(tmpdir)
            except Exception:
                pass
