#!/usr/bin/env python3
"""
Migration Script: Fix Existing Approved Parkings
This script sets is_available=True for all approved parkings that have is_available=False
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, '/home/claude/smartcity-TIMEZONE-FIX')

from models.database import Database
from datetime import datetime
import pytz

def main():
    print("=" * 70)
    print("🔧 MIGRATION: Fix Existing Approved Parkings")
    print("=" * 70)
    
    # Initialize database
    db = Database()
    
    # Get IST time
    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist).replace(tzinfo=None)
    
    print(f"\n⏰ Current Time (IST): {current_time}")
    
    # Find approved parkings that are not expired but have is_available=False
    query = {
        'status': 'approved',
        'available_to': {'$gte': current_time}
    }
    
    all_approved = list(db.find_many('parking_spaces', query))
    print(f"\n📊 Found {len(all_approved)} approved non-expired parkings")
    
    # Count how many have is_available=False
    needs_fix = [p for p in all_approved if not p.get('is_available', False)]
    print(f"⚠️  {len(needs_fix)} parkings have is_available=False (NEEDS FIX)")
    
    already_ok = [p for p in all_approved if p.get('is_available', False)]
    print(f"✅ {len(already_ok)} parkings already have is_available=True (OK)")
    
    if len(needs_fix) == 0:
        print("\n🎉 All approved parkings are already correctly configured!")
        print("No migration needed.")
        return
    
    print(f"\n📋 Parkings that will be fixed:")
    for i, parking in enumerate(needs_fix, 1):
        print(f"   {i}. {parking.get('title', 'N/A')} (ID: {parking['_id']})")
        print(f"      Current: status={parking.get('status')}, is_available={parking.get('is_available')}")
        print(f"      Will set: is_available=True")
    
    # Ask for confirmation
    print(f"\n⚠️  This will update {len(needs_fix)} parking space(s)")
    response = input("Continue? (yes/no): ").strip().lower()
    
    if response not in ['yes', 'y']:
        print("\n❌ Migration cancelled by user")
        return
    
    # Perform the fix
    print(f"\n🔧 Applying fix...")
    
    from bson.objectid import ObjectId
    fixed_count = 0
    
    for parking in needs_fix:
        try:
            result = db.update_one(
                'parking_spaces',
                {'_id': parking['_id']},
                {'$set': {
                    'is_available': True,
                    'updated_at': current_time
                }}
            )
            
            if result.modified_count > 0:
                fixed_count += 1
                print(f"   ✅ Fixed: {parking.get('title', 'N/A')} (ID: {parking['_id']})")
            else:
                print(f"   ⚠️  No changes: {parking.get('title', 'N/A')} (ID: {parking['_id']})")
        
        except Exception as e:
            print(f"   ❌ Error fixing {parking['_id']}: {e}")
    
    print(f"\n" + "=" * 70)
    print(f"✅ MIGRATION COMPLETE")
    print(f"=" * 70)
    print(f"\n📊 Results:")
    print(f"   - Total approved parkings: {len(all_approved)}")
    print(f"   - Already OK: {len(already_ok)}")
    print(f"   - Needed fixing: {len(needs_fix)}")
    print(f"   - Successfully fixed: {fixed_count}")
    print(f"   - Failed: {len(needs_fix) - fixed_count}")
    
    print(f"\n💡 Next steps:")
    print(f"   1. Refresh the dashboard in your browser (Ctrl+F5)")
    print(f"   2. Check if parkings now appear in 'Available Parking Spaces'")
    print(f"   3. If still not showing, check the debug_parking.py output")
    
    print(f"\n" + "=" * 70)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Migration cancelled by user (Ctrl+C)")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
