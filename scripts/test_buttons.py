#!/usr/bin/env python3
"""
Test script to verify button creation and voting functionality
"""

import sys
sys.path.append('..')

from handlers.add_handler import create_voting_blocks, format_entry_response
from services.bigquery_service import bigquery_service
import json

def test_button_creation():
    """Test if buttons are created correctly"""
    print("🧪 Testing button creation...")
    
    # Test with sample entry
    entry_id = "test-entry-123"
    current_score = 5
    
    blocks = create_voting_blocks(entry_id)
    print("✅ Voting blocks created:")
    print(json.dumps(blocks, indent=2))
    
    return blocks

def test_entry_response_format():
    """Test if entry response format is correct"""
    print("\n🧪 Testing entry response format...")
    
    # Get an actual entry from the database
    entries = bigquery_service.list_entries(None, 1)
    if not entries:
        print("❌ No entries found in database")
        return None
    
    entry = entries[0]
    print(f"Found entry: {entry['title']} (ID: {entry['id']})")
    
    # Get entry with score
    entry_with_score = bigquery_service.get_entry_with_score(entry['id'])
    if not entry_with_score:
        print("❌ Could not get entry with score")
        return None
    
    print(f"Entry with score: {entry_with_score['score']}")
    
    # Format the response
    response = format_entry_response(entry_with_score)
    print("✅ Entry response formatted:")
    print(json.dumps(response, indent=2))
    
    return response

def test_voting_logic():
    """Test voting logic"""
    print("\n🧪 Testing voting logic...")
    
    entries = bigquery_service.list_entries(None, 1)
    if not entries:
        print("❌ No entries found")
        return
    
    entry_id = entries[0]['id']
    test_user = "test_user_debug"
    
    print(f"Testing vote on entry: {entry_id}")
    
    # Test upvote
    result = bigquery_service.add_or_update_vote(entry_id, test_user, 1)
    print(f"Upvote result: {result}")
    
    # Get updated score
    entry = bigquery_service.get_entry_with_score(entry_id)
    if entry:
        print(f"New score after upvote: {entry['score']}")
    
    # Test downvote
    result = bigquery_service.add_or_update_vote(entry_id, test_user, -1)
    print(f"Downvote result: {result}")
    
    # Get updated score
    entry = bigquery_service.get_entry_with_score(entry_id)
    if entry:
        print(f"New score after downvote: {entry['score']}")

if __name__ == "__main__":
    print("🔍 Button Debugging Test Suite")
    print("=" * 50)
    
    try:
        test_button_creation()
        test_entry_response_format() 
        test_voting_logic()
        print("\n✅ All tests completed!")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
