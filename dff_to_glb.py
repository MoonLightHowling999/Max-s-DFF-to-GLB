import sys, os, argparse, configparser, subprocess, logging, shutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger()

WORKER = Path(__file__).resolve().parent / "blender_worker.py"

def load_cfg(path):
    cfg = configparser.ConfigParser()
    cfg.read(path)
    p = cfg["paths"] if "paths" in cfg else {}

    src = p.get("source_folder", "").strip()
    dst = p.get("destination_folder", "").strip()
    if not src or not dst:
        sys.exit("source_folder and destination_folder must be set in converter.cfg")

    src = Path(src).expanduser().resolve()
    dst = Path(dst).expanduser().resolve()
    if not src.is_dir():
        sys.exit(f"source folder doesn't exist: {src}")

    blender = p.get("blender_exe", "blender").strip() or "blender"
    dragonff_raw = p.get("dragonff_path", "").strip()

    if dragonff_raw:
        dragonff = Path(dragonff_raw).expanduser().resolve()
    else:
        here = Path(__file__).resolve().parent
        dragonff = next((x for x in [here/"DragonFF-master", here/"DragonFF", here/"dragonff"] if x.is_dir()), None)
        if not dragonff:
            sys.exit("can't find DragonFF folder - set dragonff_path in converter.cfg")
        log.info("found DragonFF at %s", dragonff)

    if not (dragonff / "__init__.py").exists():
        sys.exit(f"dragonff_path doesn't look right (no __init__.py): {dragonff}")

    if not shutil.which(blender) and not Path(blender).exists():
        sys.exit(f"blender not found: {blender}\nset blender_exe in converter.cfg")

    dst.mkdir(parents=True, exist_ok=True)
    return src, dst, blender, dragonff


def do_file(dff, out, blender, dragonff, timeout):
    env = os.environ.copy()
    env["DFF_INPUT"]  = str(dff)
    env["DFF_OUTPUT"] = str(out)
    env["DFF_ADDON"]  = str(dragonff)
    try:
        r = subprocess.run(
            [blender, "--background", "--factory-startup", "--python", str(WORKER), "--"],
            env=env, capture_output=True, text=True, timeout=timeout
        )
        if r.returncode == 0 and out.exists():
            return dff.stem, True, f"{out.stat().st_size:,}b"
        return dff.stem, False, (r.stdout + r.stderr).strip()
    except subprocess.TimeoutExpired:
        return dff.stem, False, f"timed out ({timeout}s)"
    except Exception as e:
        return dff.stem, False, str(e)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config",      "-c", default="converter.cfg")
    ap.add_argument("--workers",     "-j", type=int, default=4)
    ap.add_argument("--timeout",     "-t", type=int, default=120)
    ap.add_argument("--init-config", action="store_true")
    ap.add_argument("--debug",       "-d", metavar="file.dff")
    args = ap.parse_args()

    if args.init_config:
        open(args.config, "w").write(
            "[paths]\n"
            "source_folder      = C:/SA/models\n"
            "destination_folder = C:/SA/models/glb\n"
            "blender_exe        = C:/Program Files/Blender Foundation/Blender 5.1/blender.exe\n"
            "dragonff_path      = C:/tools/DragonFF-master\n"
        )
        log.info("wrote %s", args.config)
        return

    if not Path(args.config).exists():
        sys.exit(f"no config found, run with --init-config to create one")

    src, dst, blender, dragonff = load_cfg(args.config)

    if not WORKER.exists():
        sys.exit(f"blender_worker.py not found next to this script ({WORKER})")

    if args.debug:
        dff = Path(args.debug).resolve()
        if not dff.exists():
            hits = list(src.rglob(Path(args.debug).name))
            if not hits: sys.exit(f"file not found: {args.debug}")
            dff = hits[0]
        out = dst / dff.with_suffix(".glb").name
        log.info("debug: %s -> %s", dff, out)
        env = os.environ.copy()
        env["DFF_INPUT"]  = str(dff)
        env["DFF_OUTPUT"] = str(out)
        env["DFF_ADDON"]  = str(dragonff)
        subprocess.run(
            [blender, "--background", "--factory-startup", "--python", str(WORKER), "--"],
            env=env
        )
        return

    dffs = sorted(src.rglob("*.dff"))
    if not dffs:
        sys.exit(f"no .dff files in {src}")

    jobs = [(d, dst / d.relative_to(src).with_suffix(".glb")) for d in dffs]
    skip = [(d, o) for d, o in jobs if o.exists() and o.stat().st_size > 0]
    jobs = [(d, o) for d, o in jobs if not (o.exists() and o.stat().st_size > 0)]

    log.info("%d dffs total, %d already done, converting %d", len(dffs), len(skip), len(jobs))
    log.info("blender: %s", blender)

    if not jobs:
        log.info("nothing to do")
        return

    ok = fail = done = 0
    failed = []

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        fs = {pool.submit(do_file, d, o, blender, dragonff, args.timeout): d for d, o in jobs}
        for f in as_completed(fs):
            stem, good, msg = f.result()
            done += 1
            pct = done * 100 // len(jobs)
            if good:
                ok += 1
                log.info("[%3d%%] ok    %s  (%s)", pct, stem, msg)
            else:
                fail += 1
                failed.append((stem, msg))
                log.error("[%3d%%] FAIL  %s\n%s", pct, stem, msg)

    log.info("done — %d ok, %d failed out of %d", ok, fail, len(jobs))
    if failed:
        log.info("failures:")
        for stem, msg in failed:
            log.info("  %s: %s", stem, msg[:200])

if __name__ == "__main__":
    main()