#!/usr/bin/env python3
"""
Enhanced Pipeline Monitor
=========================

Real-time monitoring script for the enhanced comprehensive pipeline.
"""

import os
import subprocess
import time
from datetime import datetime


def check_pipeline_status():
    """Check if any pipeline is running"""
    try:
        result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
        pipelines_running = []

        if "enhanced_comprehensive_pipeline.py" in result.stdout:
            pipelines_running.append("Enhanced Comprehensive Pipeline")
        if "comprehensive_news_pipeline.py" in result.stdout:
            pipelines_running.append("Comprehensive News Pipeline")
        if "enhanced_crypto_macro_extractor.py" in result.stdout:
            pipelines_running.append("Crypto Macro Extractor")

        return pipelines_running
    except Exception:
        return []


def get_extraction_progress():
    """Get progress from extraction logs"""
    try:
        log_files = ["enhanced_crypto_macro.log", "enhanced_comprehensive_pipeline.log"]
        progress = {}

        for log_file in log_files:
            if os.path.exists(log_file):
                with open(log_file, "r") as f:
                    lines = f.readlines()

                progress[log_file] = {
                    "total_lines": len(lines),
                    "last_10_lines": lines[-10:] if lines else [],
                    "articles_extracted": sum(1 for line in lines if "✅ Added" in line),
                    "crypto_articles": sum(1 for line in lines if "✅ Added crypto article" in line),
                    "macro_articles": sum(1 for line in lines if "✅ Added macro article" in line),
                    "sources_processed": sum(1 for line in lines if "articles extracted" in line),
                    "errors": sum(1 for line in lines if "ERROR" in line or "❌" in line),
                }

        return progress
    except Exception as e:
        return {"error": str(e)}


def check_results():
    """Check what results have been generated"""
    results = {}

    # Check various result directories
    dirs_to_check = [
        "enhanced_results",
        "crypto_macro_results",
        "comprehensive_results",
    ]

    for dir_name in dirs_to_check:
        if os.path.exists(dir_name):
            files = os.listdir(dir_name)
            results[dir_name] = {
                "file_count": len(files),
                "files": files,
                "total_size": sum(
                    os.path.getsize(os.path.join(dir_name, f)) for f in files if os.path.isfile(os.path.join(dir_name, f))
                ),
            }
        else:
            results[dir_name] = {"file_count": 0, "files": [], "total_size": 0}

    return results


def main():
    print("🔍 ENHANCED PIPELINE MONITORING SYSTEM")
    print("=" * 70)
    print(f"📅 Current time: {datetime.now()}")
    print()

    # Check running pipelines
    running_pipelines = check_pipeline_status()
    print("🚀 RUNNING PIPELINES:")
    if running_pipelines:
        for pipeline in running_pipelines:
            print(f"   ✅ {pipeline}")
    else:
        print("   ❌ No pipelines currently running")
    print()

    # Get extraction progress
    print("📊 EXTRACTION PROGRESS:")
    progress = get_extraction_progress()

    if "enhanced_crypto_macro.log" in progress:
        log_data = progress["enhanced_crypto_macro.log"]
        print(f"   📰 Total articles extracted: {log_data['articles_extracted']}")
        print(f"   🪙 Crypto articles: {log_data['crypto_articles']}")
        print(f"   💰 Macro articles: {log_data['macro_articles']}")
        print(f"   📡 Sources processed: {log_data['sources_processed']}")
        print(f"   ❌ Errors encountered: {log_data['errors']}")

        print(f"\n📝 LATEST ACTIVITY (last 5 lines):")
        for line in log_data["last_10_lines"][-5:]:
            if line.strip():
                timestamp = line.split(" - ")[0] if " - " in line else ""
                message = line.split(" - ")[-1].strip() if " - " in line else line.strip()
                print(f"   {timestamp.split()[1] if timestamp else ''}: {message[:80]}...")
    else:
        print("   📝 No extraction log found yet")
    print()

    # Check results
    print("📁 GENERATED RESULTS:")
    results = check_results()

    total_files = 0
    total_size = 0

    for dir_name, dir_data in results.items():
        file_count = dir_data["file_count"]
        size_mb = dir_data["total_size"] / (1024 * 1024) if dir_data["total_size"] > 0 else 0

        print(f"   📂 {dir_name}/: {file_count} files ({size_mb:.1f} MB)")

        if file_count > 0:
            for file in dir_data["files"][:3]:  # Show first 3 files
                print(f"      📄 {file}")
            if file_count > 3:
                print(f"      ... and {file_count - 3} more files")

        total_files += file_count
        total_size += dir_data["total_size"]

    total_size_mb = total_size / (1024 * 1024) if total_size > 0 else 0
    print(f"\n📈 TOTAL: {total_files} files, {total_size_mb:.1f} MB generated")
    print()

    # Show process info
    print("🔍 PROCESS INFORMATION:")
    try:
        result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
        lines = result.stdout.split("\n")
        python_processes = [
            line for line in lines if "python" in line.lower() and ("enhanced" in line or "comprehensive" in line)
        ]

        if python_processes:
            for proc in python_processes:
                parts = proc.split()
                if len(parts) >= 11:
                    cpu = parts[2]
                    mem = parts[3]
                    time_str = parts[9]
                    command = " ".join(parts[10:])
                    print(f"   🔄 CPU: {cpu}% | MEM: {mem}% | TIME: {time_str} | {command[:50]}...")
        else:
            print("   💤 No relevant processes found")
    except Exception:
        print("   ❓ Could not check process information")

    print()
    print("=" * 70)
    print("💡 INSTRUCTIONS:")
    print("   📊 To view live logs: tail -f enhanced_crypto_macro.log")
    print("   🔄 To check results: ls -la enhanced_results/")
    print("   ⏹️  To stop pipeline: kill [process_id]")
    print("   🔄 Re-run this monitor: python3 enhanced_monitor.py")


if __name__ == "__main__":
    main()
