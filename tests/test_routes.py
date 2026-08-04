
from app import create_app
from flask import url_for

app = create_app('testing')
app.config['SERVER_NAME'] = 'localhost'

with app.app_context():
    print("Testing URL generation...")
    try:
        # Testing Community routes
        print(f"Community Index: {url_for('community.index')}")
        # These are likely to fail based on exploration
        try:
            print(f"Community Category (correct param): {url_for('community.category', category_id=1)}")
        except Exception as e:
            print(f"Community Category (correct param) FAILED: {e}")
            
        # Testing Chat routes
        print(f"Chat Index: {url_for('chat.index')}")
        try:
            print(f"Chat Channel: {url_for('chat.channel', channel_id=1)}")
        except Exception as e:
            print(f"Chat Channel FAILED: {e}")
            
        try:
            print(f"Chat Send Message: {url_for('chat.send_message')}")
        except Exception as e:
            print(f"Chat Send Message FAILED: {e}")

    except Exception as e:
        print(f"General URL generation error: {e}")
