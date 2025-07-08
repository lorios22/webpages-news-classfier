#!/usr/bin/env python3
"""
Debug script to test Slack API access and channel permissions
"""

import os
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Load environment variables
load_dotenv()

def test_slack_connection():
    """Test basic Slack API connection"""
    print("🔍 Testing Slack API Connection...")
    
    token = os.getenv('SLACK_BOT_TOKEN')
    if not token:
        print("❌ SLACK_BOT_TOKEN not found in environment")
        return False
    
    print(f"✅ Bot token found: {token[:20]}...")
    
    try:
        client = WebClient(token=token)
        
        # Test auth
        auth_response = client.auth_test()
        if auth_response["ok"]:
            print(f"✅ Bot authenticated successfully")
            print(f"   Bot User ID: {auth_response['user_id']}")
            print(f"   Bot Name: {auth_response['user']}")
            print(f"   Team: {auth_response['team']}")
            return client
        else:
            print(f"❌ Authentication failed: {auth_response}")
            return False
            
    except SlackApiError as e:
        print(f"❌ Slack API Error: {e.response['error']}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_channel_access(client, channel_id):
    """Test access to specific channel"""
    print(f"\n🔍 Testing Channel Access: {channel_id}")
    
    try:
        # Try to get channel info
        channel_info = client.conversations_info(channel=channel_id)
        if channel_info["ok"]:
            channel = channel_info["channel"]
            print(f"✅ Channel found: #{channel['name']}")
            print(f"   Channel ID: {channel['id']}")
            print(f"   Is Member: {channel.get('is_member', False)}")
            
            if not channel.get('is_member', False):
                print(f"⚠️  Bot is NOT a member of this channel")
                print(f"   Solution: Invite bot to channel with /invite @{client.auth_test()['user']}")
            
            return channel.get('is_member', False)
        else:
            print(f"❌ Cannot access channel: {channel_info}")
            return False
            
    except SlackApiError as e:
        error_msg = e.response['error']
        print(f"❌ Channel access error: {error_msg}")
        
        if error_msg == "channel_not_found":
            print("   Channel ID might be incorrect or bot lacks permission")
        elif error_msg == "not_in_channel":
            print("   Bot needs to be invited to the channel")
        elif error_msg == "missing_scope":
            print("   Bot lacks required OAuth scopes")
            
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_message_history(client, channel_id):
    """Test reading message history from channel"""
    print(f"\n🔍 Testing Message History Access...")
    
    try:
        # Try to get recent messages
        history = client.conversations_history(
            channel=channel_id,
            limit=5
        )
        
        if history["ok"]:
            messages = history["messages"]
            print(f"✅ Successfully read {len(messages)} recent messages")
            
            # Count messages with URLs
            url_messages = []
            for msg in messages:
                text = msg.get('text', '')
                if 'http' in text:
                    url_messages.append(msg)
            
            print(f"   Messages with URLs: {len(url_messages)}")
            return True
        else:
            print(f"❌ Cannot read message history: {history}")
            return False
            
    except SlackApiError as e:
        print(f"❌ Message history error: {e.response['error']}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main debug function"""
    print("=" * 50)
    print("SLACK API DEBUG TOOL")
    print("=" * 50)
    
    # Test basic connection
    client = test_slack_connection()
    if not client:
        print("\n❌ Cannot continue - fix bot token first")
        return
    
    # Get channel IDs from config
    source_channel = os.getenv('SLACK_CHANNEL_SOURCE', 'C05UB8G8B0F')
    target_channel = os.getenv('SLACK_CHANNEL_TARGET', 'C08E29EEWE5')
    
    print(f"\nTesting channels from configuration:")
    print(f"Source: {source_channel}")
    print(f"Target: {target_channel}")
    
    # Test source channel (where URLs are extracted)
    print(f"\n{'=' * 30}")
    print("TESTING SOURCE CHANNEL")
    print(f"{'=' * 30}")
    source_access = test_channel_access(client, source_channel)
    
    if source_access:
        test_message_history(client, source_channel)
    
    # Test target channel (where results are posted)
    print(f"\n{'=' * 30}")
    print("TESTING TARGET CHANNEL")
    print(f"{'=' * 30}")
    target_access = test_channel_access(client, target_channel)
    
    # Summary
    print(f"\n{'=' * 50}")
    print("SUMMARY")
    print(f"{'=' * 50}")
    print(f"Source Channel Access: {'✅' if source_access else '❌'}")
    print(f"Target Channel Access: {'✅' if target_access else '❌'}")
    
    if source_access and target_access:
        print("\n🎉 All Slack access tests passed!")
        print("   Pipeline should work correctly now")
    else:
        print("\n⚠️  Some access issues found")
        print("   Fix channel access before running pipeline")

if __name__ == "__main__":
    main() 