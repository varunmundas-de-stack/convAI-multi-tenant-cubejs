"""
Quick script to check ChromaDB sync status
"""
from vector_store.chromadb_client import get_chroma_client

print("\n" + "=" * 70)
print("ChromaDB Sync Status Check")
print("=" * 70 + "\n")

client = get_chroma_client()
collections = client.list_collections()

# Filter for duckdb collections
duckdb_collections = [c for c in collections if c.startswith('duckdb_')]

print(f"Total DuckDB collections: {len(duckdb_collections)}\n")
print(f"{'Collection Name':<35} {'Document Count':<20}")
print("-" * 70)

total_docs = 0
for collection_name in sorted(duckdb_collections):
    stats = client.get_collection_stats(collection_name)
    count = stats['count']
    total_docs += count

    # Extract table name
    table_name = collection_name.replace('duckdb_', '')

    print(f"{table_name:<35} {count:<20}")

print("-" * 70)
print(f"{'TOTAL':<35} {total_docs:<20}")

print("\n" + "=" * 70)
print("Expected Counts:")
print("=" * 70)
expected = {
    'dim_date': 90,
    'dim_product': 50,
    'dim_geography': 200,
    'dim_customer': 120,
    'dim_channel': 5,
    'fact_secondary_sales': 1000,
}

print(f"\n{'Table':<35} {'Expected':<15} {'Actual':<15} {'Status':<10}")
print("-" * 70)

all_good = True
for table, expected_count in expected.items():
    collection_name = f"duckdb_{table}"
    if collection_name in duckdb_collections:
        stats = client.get_collection_stats(collection_name)
        actual_count = stats['count']
        status = "[OK]" if actual_count == expected_count else "[WARN]"
        if actual_count != expected_count:
            all_good = False
        print(f"{table:<35} {expected_count:<15} {actual_count:<15} {status:<10}")
    else:
        print(f"{table:<35} {expected_count:<15} {'MISSING':<15} [ERROR]")
        all_good = False

print("-" * 70)
if all_good:
    print("\n[OK] All tables synced correctly!")
else:
    print("\n[WARN] Some tables need re-syncing. Run: python vector_store/sync_duckdb_to_chroma.py")

print("\n" + "=" * 70 + "\n")
