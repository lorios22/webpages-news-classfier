#!/usr/bin/env python3
"""
Historical Archive Manager
==========================

Automatically manages historical archiving of pipeline results.
Moves completed results to historical folders and keeps working directories clean.

Features:
- Automatic archiving of enhanced_results to historical folders
- Timestamped historical folders
- Clean working directory management
- Pre-execution cleanup
- Comprehensive logging

Author: AI Assistant
Version: 1.0.0
License: MIT
"""

import json
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("archive_manager.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class HistoricalArchiveManager:
    """Manages historical archiving of pipeline results"""

    def __init__(self):
        """Initialize the archive manager"""
        self.working_dirs = [
            "enhanced_results",
            "crypto_macro_results",
            "comprehensive_results",
            "integrated_crypto_macro_results",
        ]

        self.historical_base = "historical_archives"
        self.current_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Ensure historical base directory exists
        os.makedirs(self.historical_base, exist_ok=True)

        logger.info("🗄️ Historical Archive Manager initialized")
        logger.info(f"📁 Monitoring directories: {', '.join(self.working_dirs)}")
        logger.info(f"🏛️ Historical base: {self.historical_base}")

    def check_existing_results(self) -> Dict[str, List[str]]:
        """Check which working directories have existing results"""
        existing_results = {}

        for dir_name in self.working_dirs:
            if os.path.exists(dir_name):
                files = [f for f in os.listdir(dir_name) if os.path.isfile(os.path.join(dir_name, f))]
                if files:
                    existing_results[dir_name] = files
                    logger.info(f"📊 Found {len(files)} files in {dir_name}/")
                else:
                    logger.info(f"📂 {dir_name}/ is empty")
            else:
                logger.info(f"📂 {dir_name}/ does not exist")

        return existing_results

    def archive_directory(self, source_dir: str, archive_timestamp: str = None) -> Optional[str]:
        """Archive a directory to historical storage"""
        if not os.path.exists(source_dir):
            logger.warning(f"⚠️ Source directory {source_dir} does not exist")
            return None

        files = [f for f in os.listdir(source_dir) if os.path.isfile(os.path.join(source_dir, f))]
        if not files:
            logger.info(f"📂 {source_dir}/ is empty, nothing to archive")
            return None

        # Use provided timestamp or current one
        timestamp = archive_timestamp or self.current_timestamp

        # Create historical directory
        historical_dir = os.path.join(self.historical_base, f"{source_dir}_{timestamp}")
        os.makedirs(historical_dir, exist_ok=True)

        # Move files to historical directory
        moved_files = []
        for file_name in files:
            src_file = os.path.join(source_dir, file_name)
            dst_file = os.path.join(historical_dir, file_name)

            try:
                shutil.move(src_file, dst_file)
                moved_files.append(file_name)
                logger.debug(f"📦 Moved: {file_name}")
            except Exception as e:
                logger.error(f"❌ Error moving {file_name}: {str(e)}")

        if moved_files:
            logger.info(f"✅ Archived {len(moved_files)} files from {source_dir}/ to {historical_dir}/")

            # Create archive manifest
            manifest = {
                "archive_timestamp": timestamp,
                "source_directory": source_dir,
                "archived_files": moved_files,
                "archive_date": datetime.now().isoformat(),
                "file_count": len(moved_files),
            }

            manifest_file = os.path.join(historical_dir, "archive_manifest.json")
            with open(manifest_file, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)

            return historical_dir
        else:
            # Remove empty historical directory
            os.rmdir(historical_dir)
            return None

    def archive_all_existing_results(self) -> Dict[str, str]:
        """Archive all existing results to historical storage"""
        logger.info("🗄️ Starting archive of all existing results")
        logger.info("=" * 60)

        archived_dirs = {}
        archive_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        for dir_name in self.working_dirs:
            historical_dir = self.archive_directory(dir_name, archive_timestamp)
            if historical_dir:
                archived_dirs[dir_name] = historical_dir

        if archived_dirs:
            logger.info("✅ Archive completed successfully")
            logger.info(f"📊 Archived {len(archived_dirs)} directories")
            for source, historical in archived_dirs.items():
                logger.info(f"   📁 {source} → {historical}")
        else:
            logger.info("📂 No results found to archive")

        return archived_dirs

    def prepare_clean_working_directories(self) -> List[str]:
        """Prepare clean working directories for new pipeline execution"""
        logger.info("🧹 Preparing clean working directories")

        cleaned_dirs = []

        for dir_name in self.working_dirs:
            # Create directory if it doesn't exist
            os.makedirs(dir_name, exist_ok=True)

            # Verify it's empty
            files = [f for f in os.listdir(dir_name) if os.path.isfile(os.path.join(dir_name, f))]
            if files:
                logger.warning(f"⚠️ {dir_name}/ still contains {len(files)} files after archiving")
            else:
                logger.info(f"✅ {dir_name}/ is clean and ready")
                cleaned_dirs.append(dir_name)

        return cleaned_dirs

    def pre_execution_cleanup(self) -> Dict[str, any]:
        """Perform pre-execution cleanup and archiving"""
        logger.info("🚀 PRE-EXECUTION CLEANUP STARTING")
        logger.info("=" * 60)

        # Check existing results
        existing_results = self.check_existing_results()

        # Archive existing results if any
        archived_dirs = {}
        if existing_results:
            logger.info(f"📊 Found existing results in {len(existing_results)} directories")
            archived_dirs = self.archive_all_existing_results()
        else:
            logger.info("📂 No existing results found")

        # Prepare clean directories
        cleaned_dirs = self.prepare_clean_working_directories()

        # Summary
        summary = {
            "existing_results_found": len(existing_results),
            "directories_archived": len(archived_dirs),
            "directories_cleaned": len(cleaned_dirs),
            "archived_directories": archived_dirs,
            "timestamp": datetime.now().isoformat(),
        }

        logger.info("✅ PRE-EXECUTION CLEANUP COMPLETED")
        logger.info(
            f"📊 Summary: {len(existing_results)} existing, {len(archived_dirs)} archived, {len(cleaned_dirs)} cleaned"
        )

        return summary

    def post_execution_archive(self, results_dir: str = "enhanced_results") -> Optional[str]:
        """Archive results after successful pipeline execution"""
        logger.info(f"📦 POST-EXECUTION ARCHIVING: {results_dir}")

        if not os.path.exists(results_dir):
            logger.warning(f"⚠️ Results directory {results_dir} not found")
            return None

        files = [f for f in os.listdir(results_dir) if os.path.isfile(os.path.join(results_dir, f))]
        if not files:
            logger.info(f"📂 {results_dir}/ is empty, nothing to archive")
            return None

        # Archive with current timestamp
        historical_dir = self.archive_directory(results_dir)

        if historical_dir:
            logger.info(f"✅ Results archived to: {historical_dir}")
            return historical_dir
        else:
            logger.warning("⚠️ Failed to archive results")
            return None

    def list_historical_archives(self) -> List[Dict]:
        """List all historical archives"""
        archives = []

        if not os.path.exists(self.historical_base):
            return archives

        for item in os.listdir(self.historical_base):
            archive_path = os.path.join(self.historical_base, item)
            if os.path.isdir(archive_path):
                manifest_file = os.path.join(archive_path, "archive_manifest.json")
                if os.path.exists(manifest_file):
                    try:
                        with open(manifest_file, "r", encoding="utf-8") as f:
                            manifest = json.load(f)
                        manifest["archive_path"] = archive_path
                        archives.append(manifest)
                    except Exception as e:
                        logger.error(f"❌ Error reading manifest for {item}: {str(e)}")

        # Sort by archive date
        archives.sort(key=lambda x: x.get("archive_date", ""), reverse=True)
        return archives

    def cleanup_old_archives(self, keep_days: int = 30) -> int:
        """Clean up archives older than specified days"""
        from datetime import datetime, timedelta

        cutoff_date = datetime.now() - timedelta(days=keep_days)
        archives = self.list_historical_archives()

        removed_count = 0
        for archive in archives:
            try:
                archive_date = datetime.fromisoformat(archive["archive_date"].replace("Z", "+00:00"))
                if archive_date < cutoff_date:
                    archive_path = archive["archive_path"]
                    shutil.rmtree(archive_path)
                    logger.info(f"🗑️ Removed old archive: {os.path.basename(archive_path)}")
                    removed_count += 1
            except Exception as e:
                logger.error(f"❌ Error removing archive: {str(e)}")

        if removed_count > 0:
            logger.info(f"✅ Cleaned up {removed_count} old archives")
        else:
            logger.info("📂 No old archives to clean up")

        return removed_count


def main():
    """Main execution function for testing"""
    print("🗄️ HISTORICAL ARCHIVE MANAGER")
    print("=" * 50)

    manager = HistoricalArchiveManager()

    # Perform pre-execution cleanup
    summary = manager.pre_execution_cleanup()

    print(f"\n📊 CLEANUP SUMMARY:")
    print(f"   📂 Existing results: {summary['existing_results_found']}")
    print(f"   📦 Directories archived: {summary['directories_archived']}")
    print(f"   🧹 Directories cleaned: {summary['directories_cleaned']}")

    if summary["archived_directories"]:
        print(f"\n📁 ARCHIVED DIRECTORIES:")
        for source, historical in summary["archived_directories"].items():
            print(f"   {source} → {os.path.basename(historical)}")

    # List existing historical archives
    archives = manager.list_historical_archives()
    if archives:
        print(f"\n🏛️ HISTORICAL ARCHIVES ({len(archives)} total):")
        for archive in archives[:5]:  # Show latest 5
            print(f"   📦 {os.path.basename(archive['archive_path'])} - {archive['file_count']} files")
        if len(archives) > 5:
            print(f"   ... and {len(archives) - 5} more archives")
    else:
        print(f"\n🏛️ No historical archives found")


if __name__ == "__main__":
    main()
