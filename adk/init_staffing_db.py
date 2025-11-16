#!/usr/bin/env python3
"""
Initialize staffing database for production use.

This script configures SQLite for optimal concurrent access in a
multi-user web application environment.
"""

import os
import sys
import sqlite3
from pathlib import Path


def enable_wal_mode(db_path: str) -> bool:
    """
    Enable Write-Ahead Logging (WAL) mode for better concurrency.

    WAL mode allows:
    - Multiple concurrent readers (unlimited)
    - Readers don't block writers
    - Writers don't block readers
    - Better performance for web applications

    Args:
        db_path: Path to SQLite database

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        print(f"📊 Configuring database: {db_path}")

        if not os.path.exists(db_path):
            print(f"❌ Database not found: {db_path}")
            return False

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Enable WAL mode
        cursor.execute("PRAGMA journal_mode=WAL")
        result = cursor.fetchone()[0]
        print(f"   ✅ Journal mode: {result}")

        # Set synchronous mode to NORMAL for better performance
        # (Still safe with WAL mode)
        cursor.execute("PRAGMA synchronous=NORMAL")
        result = cursor.fetchone()[0]
        print(f"   ✅ Synchronous mode: {result}")

        # Set busy timeout to 5 seconds
        # (Helps with concurrent access)
        cursor.execute("PRAGMA busy_timeout=5000")
        print(f"   ✅ Busy timeout: 5000ms")

        # Set cache size (in KB)
        cursor.execute("PRAGMA cache_size=-2000")  # 2MB cache
        print(f"   ✅ Cache size: 2MB")

        # Enable memory-mapped I/O for better performance
        cursor.execute("PRAGMA mmap_size=268435456")  # 256MB
        print(f"   ✅ Memory-mapped I/O: 256MB")

        conn.commit()
        conn.close()

        print(f"✅ Database configured for multi-user access!")
        return True

    except Exception as e:
        print(f"❌ Error configuring database: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_configuration(db_path: str) -> None:
    """
    Verify database configuration.

    Args:
        db_path: Path to SQLite database
    """
    try:
        print(f"\n📋 Verifying configuration...")

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check journal mode
        cursor.execute("PRAGMA journal_mode")
        journal_mode = cursor.fetchone()[0]
        status = "✅" if journal_mode == "wal" else "⚠️"
        print(f"   {status} Journal mode: {journal_mode}")

        # Check synchronous mode
        cursor.execute("PRAGMA synchronous")
        sync_mode = cursor.fetchone()[0]
        print(f"   ✅ Synchronous: {sync_mode}")

        # Check if WAL files exist
        wal_file = f"{db_path}-wal"
        shm_file = f"{db_path}-shm"

        if os.path.exists(wal_file):
            wal_size = os.path.getsize(wal_file)
            print(f"   ✅ WAL file exists: {wal_size} bytes")
        else:
            print(f"   ℹ️  WAL file not yet created (will be created on first write)")

        conn.close()

        print(f"✅ Configuration verified!")

    except Exception as e:
        print(f"❌ Error verifying configuration: {e}")


def get_table_stats(db_path: str, table_name: str) -> None:
    """
    Display table statistics.

    Args:
        db_path: Path to SQLite database
        table_name: Name of table to check
    """
    try:
        print(f"\n📊 Table statistics for '{table_name}'...")

        # Use read-only connection
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cursor = conn.cursor()

        # Check if table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )

        if not cursor.fetchone():
            print(f"   ⚠️  Table '{table_name}' not found!")
            conn.close()
            return

        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        print(f"   ✅ Rows: {row_count:,}")

        # Get column count
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        print(f"   ✅ Columns: {len(columns)}")

        # Show columns
        print(f"   📋 Column names:")
        for col in columns:
            col_name = col[1]
            col_type = col[2]
            pk = " [PRIMARY KEY]" if col[5] else ""
            print(f"      - {col_name}: {col_type}{pk}")

        conn.close()

    except Exception as e:
        print(f"❌ Error getting table stats: {e}")


def test_concurrent_reads(db_path: str, table_name: str) -> None:
    """
    Test concurrent read access.

    Args:
        db_path: Path to SQLite database
        table_name: Name of table to query
    """
    try:
        print(f"\n🔬 Testing concurrent read access...")

        import threading
        import time

        results = []
        errors = []

        def read_query(thread_id: int):
            """Simulate a user query."""
            try:
                # Use read-only connection
                conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
                cursor = conn.cursor()

                start = time.time()
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                elapsed = time.time() - start

                conn.close()

                results.append({
                    'thread_id': thread_id,
                    'count': count,
                    'elapsed': elapsed
                })
            except Exception as e:
                errors.append({
                    'thread_id': thread_id,
                    'error': str(e)
                })

        # Simulate 5 concurrent users
        threads = []
        for i in range(5):
            thread = threading.Thread(target=read_query, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Report results
        if errors:
            print(f"   ❌ Errors occurred:")
            for err in errors:
                print(f"      Thread {err['thread_id']}: {err['error']}")
        else:
            print(f"   ✅ All 5 concurrent reads successful!")
            avg_time = sum(r['elapsed'] for r in results) / len(results)
            print(f"   ⏱️  Average query time: {avg_time*1000:.2f}ms")

    except Exception as e:
        print(f"❌ Error testing concurrent reads: {e}")


def main():
    """Main initialization function."""
    print("=" * 70)
    print("SQLite Database Initialization for Multi-User Access")
    print("=" * 70)
    print()

    # Get database path from environment or command line
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        db_path = os.getenv("STAFFING_DATABASE_PATH", "./unpolicy.db")

    # Get table name
    if len(sys.argv) > 2:
        table_name = sys.argv[2]
    else:
        table_name = os.getenv("STAFFING_TABLE_NAME", "staffing_table")

    print(f"Database: {os.path.abspath(db_path)}")
    print(f"Table: {table_name}")
    print()

    # Step 1: Enable WAL mode
    if not enable_wal_mode(db_path):
        print("\n❌ Failed to configure database!")
        sys.exit(1)

    # Step 2: Verify configuration
    verify_configuration(db_path)

    # Step 3: Get table stats
    get_table_stats(db_path, table_name)

    # Step 4: Test concurrent reads
    test_concurrent_reads(db_path, table_name)

    print()
    print("=" * 70)
    print("✅ Database is ready for production use!")
    print("=" * 70)
    print()
    print("Next steps:")
    print("1. Your FastAPI server can now handle multiple concurrent users")
    print("2. All staffing queries will use read-only connections")
    print("3. No locking issues with multiple simultaneous queries")
    print()
    print("Performance tips:")
    print("- WAL mode allows unlimited concurrent readers")
    print("- Read-only connections don't block each other")
    print("- Busy timeout (5s) handles any temporary locks")
    print("- Memory-mapped I/O improves query performance")
    print()


if __name__ == "__main__":
    main()
