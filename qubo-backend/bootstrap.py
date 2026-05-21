"""Bootstrap script for fresh-clone setup.

Ensures all required directories and data files exist before the server starts.

Usage:
    python bootstrap.py              # Run all bootstrap steps
    python bootstrap.py --dry-run    # Show what would be done
    python bootstrap.py --force      # Force regeneration of existing files
"""

import logging
import sys
from pathlib import Path

# Add parent directory to path so we can import qubo_backend modules
sys.path.insert(0, str(Path(__file__).resolve().parent))

from generate_alpha import generate_nifty50_alpha, validate_alpha_data

logger = logging.getLogger(__name__)


def ensure_directories(base_dir: Path, dry_run: bool = False) -> list[str]:
    """Ensure all required directories exist.

    Args:
        base_dir: Project root directory
        dry_run: If True, only log what would be created

    Returns:
        List of directories created (or would be created)
    """
    dirs = [
        base_dir / "output",
        base_dir / "output" / "jobs",
        base_dir / "cache",
        base_dir / "logs",
        base_dir / "checkpoints",
    ]

    created = []
    for d in dirs:
        if not d.exists():
            if dry_run:
                logger.info("[DRY RUN] Would create directory: %s", d)
            else:
                d.mkdir(parents=True, exist_ok=True)
                logger.info("Created directory: %s", d)
            created.append(str(d))
        else:
            logger.debug("Directory already exists: %s", d)

    return created


def ensure_alpha_data(output_dir: Path, force: bool = False, dry_run: bool = False) -> str:
    """Ensure alpha_data.npz exists and is valid.

    Args:
        output_dir: Directory where alpha data should be stored
        force: If True, regenerate even if file exists
        dry_run: If True, only log what would be done

    Returns:
        Path to the alpha data file
    """
    alpha_path = output_dir / "alpha_data.npz"

    if alpha_path.exists() and not force:
        if validate_alpha_data(alpha_path):
            logger.info("Alpha data file exists and is valid: %s", alpha_path)
            return str(alpha_path)
        else:
            logger.warning("Alpha data file exists but is invalid, regenerating: %s", alpha_path)

    if dry_run:
        logger.info("[DRY RUN] Would generate alpha data at: %s", alpha_path)
        return str(alpha_path)

    path = generate_nifty50_alpha(output_dir=output_dir, force=True)

    if not validate_alpha_data(path):
        raise RuntimeError(f"Alpha data generation failed validation: {path}")

    return str(path)


def bootstrap(base_dir: Path | None = None, force: bool = False, dry_run: bool = False) -> dict:
    """Run all bootstrap steps.

    Args:
        base_dir: Project root directory. Defaults to parent of this script.
        force: If True, force regeneration of existing files
        dry_run: If True, only log what would be done

    Returns:
        Dictionary with bootstrap results
    """
    if base_dir is None:
        base_dir = Path(__file__).resolve().parent.parent

    logger.info("=" * 60)
    logger.info("QUBO Portfolio Optimizer - Bootstrap")
    logger.info("=" * 60)
    logger.info("Base directory: %s", base_dir)
    logger.info("Force: %s", force)
    logger.info("Dry run: %s", dry_run)

    result = {
        "directories_created": [],
        "alpha_data_path": None,
        "alpha_data_valid": False,
        "errors": [],
    }

    try:
        # Step 1: Ensure directories
        logger.info("\n[Step 1/2] Ensuring required directories...")
        result["directories_created"] = ensure_directories(base_dir, dry_run=dry_run)
        logger.info("Directories ready: %d created (or all exist)", len(result["directories_created"]))

        # Step 2: Ensure alpha data
        logger.info("\n[Step 2/2] Ensuring alpha data...")
        output_dir = base_dir / "output"
        result["alpha_data_path"] = ensure_alpha_data(output_dir, force=force, dry_run=dry_run)
        result["alpha_data_valid"] = validate_alpha_data(Path(result["alpha_data_path"]))

        logger.info("\n" + "=" * 60)
        logger.info("Bootstrap complete!")
        logger.info("=" * 60)
        logger.info("Alpha data: %s", result["alpha_data_path"])
        logger.info("Alpha data valid: %s", result["alpha_data_valid"])
        logger.info("Directories created: %d", len(result["directories_created"]))

    except Exception as e:
        error_msg = f"Bootstrap failed: {e}"
        logger.error(error_msg)
        result["errors"].append(error_msg)
        raise

    return result


if __name__ == "__main__":
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    parser = argparse.ArgumentParser(description="Bootstrap QUBO Portfolio Optimizer")
    parser.add_argument("--base-dir", type=str, default=None, help="Project root directory")
    parser.add_argument("--force", action="store_true", help="Force regeneration of existing files")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    args = parser.parse_args()

    base_dir = Path(args.base_dir) if args.base_dir else None

    try:
        result = bootstrap(base_dir=base_dir, force=args.force, dry_run=args.dry_run)
        if result["errors"]:
            print(f"\nBootstrap completed with {len(result['errors'])} error(s)")
            sys.exit(1)
        else:
            print("\nBootstrap completed successfully!")
            sys.exit(0)
    except Exception as e:
        print(f"\nBootstrap failed: {e}")
        sys.exit(1)
