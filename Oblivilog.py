import sanitise
import pandas as pd
import re
import glob
import logging
from typing import List, Dict
import os
import json

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# User configuration
TARGET_USERS = ['']  # Targeted users show up in the console, showing their message count. this is used for debugging.
TOP_USERS_COUNT = 50  # Number of top users to visualize

def parse_chat_data(file_path: str) -> pd.DataFrame:
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            chat_data = file.readlines()
    except Exception as e:
        logging.error(f"Error reading file {file_path}: {str(e)}")
        return pd.DataFrame(columns=['timestamp', 'username', 'message'])

    pattern = re.compile(r'\[(?P<timestamp>.+?)\] (?P<username>.+?): (?P<message>.+)')
    chat_entries = []

    for line in chat_data:
        match = pattern.match(line)
        if match:
            entry = match.groupdict()
            message = entry['message']

            # Filter out gift sub notifications (single and multi)
            if "gifted a Tier 1 sub to" in message or "is gifting" in message:
                continue

            # Filter out regular sub notifications without custom message
            if re.match(r'^[^:]+subscribed at Tier \d+\.$', message):
                continue

            # Keep resub messages only if they have custom message
            resub_match = re.match(r'^[^:]+subscribed at Tier \d+\. They\'ve subscribed for \d+ months?!(.*)$', message)
            if resub_match:
                # Only keep if there's additional message content after the system message
                if not resub_match.group(1).strip():
                    continue

            # Filter out bits messages that are just "cheerX" without additional content
            if re.match(r'^cheer\d+$', message.lower().strip()):
                continue

            chat_entries.append(entry)

    return pd.DataFrame(chat_entries)

def concatenate_dfs(file_paths: List[str]) -> pd.DataFrame:
    dfs = []
    for file_path in file_paths:
        dfs.append(parse_chat_data(file_path))
    return pd.concat(dfs, ignore_index=True)

def analyze_data(chat_df: pd.DataFrame) -> pd.Series:
    return chat_df['username'].value_counts()

def visualize_top_users(top_users: pd.Series, output_path: str):
    """Create a bar chart using Chart.js showing the top users by message count"""

    # Prepare data for the chart
    users = top_users.index.tolist()
    counts = top_users.values.tolist()

    # Format the numbers with commas
    formatted_counts = [f"{x:,}" for x in counts]

    # Generate HTML with Chart.js
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Chat Statistics</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            .chart-container {{
                height: 600px;
                width: 100%;
                max-width: 1200px;
                margin: 0 auto;
            }}
            body {{
                background-color: transparent;
                color: #dfe6e9;
                font-family: Arial, sans-serif;
            }}
        </style>
    </head>
    <body>
        <div class="chart-container">
            <canvas id="topUsersChart"></canvas>
        </div>
        <script>
            const ctx = document.getElementById('topUsersChart').getContext('2d');
            const chart = new Chart(ctx, {{
                type: 'bar',
                data: {{
                    labels: {json.dumps(users)},
                    datasets: [{{
                        label: 'Message Count',
                        data: {json.dumps(counts)},
                        backgroundColor: '#fd79a8',
                        hoverBackgroundColor: '#ff99cc',
                        borderColor: 'transparent',
                        borderWidth: 0
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        title: {{
                            display: true,
                            text: 'Top Users by Message Count (First {TOP_USERS_COUNT})',
                            color: '#dfe6e9',
                            font: {{
                                size: 16
                            }}
                        }},
                        tooltip: {{
                            callbacks: {{
                                label: function(context) {{
                                    return 'Messages: ' + context.raw.toLocaleString();
                                }}
                            }}
                        }}
                    }},
                    scales: {{
                        x: {{
                            ticks: {{
                                color: '#dfe6e9',
                                font: {{
                                    size: 10
                                }},
                                maxRotation: 45,
                                minRotation: 45
                            }},
                            grid: {{
                                display: false
                            }}
                        }},
                        y: {{
                            beginAtZero: true,
                            ticks: {{
                                color: '#dfe6e9',
                                font: {{
                                    size: 10
                                }},
                                callback: function(value) {{
                                    return value.toLocaleString();
                                }}
                            }},
                            grid: {{
                                color: 'rgba(223, 230, 233, 0.1)'
                            }}
                        }}
                    }}
                }}
            }});
        </script>
    </body>
    </html>
    """

    # Save the HTML file
    output_html = output_path.rsplit('.', 1)[0] + '.html'
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(html_content)

def save_user_list_to_file(message_count: pd.Series, filename: str):
    try:
        grouped = message_count.groupby(message_count).apply(lambda x: x.index.tolist()).to_dict()
        sorted_grouped = dict(sorted(grouped.items(), key=lambda item: item[0], reverse=True))

        with open(filename, 'w', encoding='utf-8') as file:
            for count, users in sorted_grouped.items():
                if len(users) == 1:
                    line = f"<li>{users[0]}: {count} messages</li>\n"
                elif len(users) == 2:
                    line = f"<li>{users[0]} and {users[1]}: {count} messages each</li>\n"
                else:
                    users_str = ', '.join(users[:-1]) + f" and {users[-1]}"
                    line = f"<li>{users_str}: {count} messages each</li>\n"
                file.write(line)
    except Exception as e:
        logging.error(f"Error writing to file {filename}: {str(e)}")

def count_emote_usage(chat_df: pd.DataFrame, emotes: List[str]) -> pd.Series:
    emote_counts = {emote: chat_df['message'].apply(lambda x: x.count(emote)).sum() for emote in emotes}
    return pd.Series(emote_counts)

def append_totals_to_file(message_count_per_user: pd.Series, filename: str):
    with open(filename, 'a', encoding='utf-8') as file:
        file.write(f"\nTotal Messages Sent: {message_count_per_user.sum()}\n")
        file.write(f"Total Participants: {len(message_count_per_user)}\n")

def save_emote_usage_to_file(emote_usage: Dict[str, int], filename: str):
    try:
        # Get top 3 emotes
        top_3_emotes = list(emote_usage.items())[:3]

        html_content = '''        <div class="emote-stats">
          <h2>Top Emotes</h2>
          <div class="emote-podium">'''

        # Position names for classes
        positions = ['first', 'second', 'third']

        for (emote, count), position in zip(top_3_emotes, positions):
            extension = 'png'

            html_content += f'''
            <div class="podium-item {position}">
              <img src="assets/emotes/{emote}.{extension}" alt="{emote}" class="emote-icon">
              <span class="emote-count">{count}</span>
            </div>'''

        html_content += '''
          </div>
        </div>
      </div>'''

        with open(filename, 'w', encoding='utf-8') as file:
            file.write(html_content)
    except Exception as e:
        logging.error(f"Error writing to file {filename}: {str(e)}")

def process_streamer_data(streamer_path: str):
    """Process chat data for a single streamer."""
    streamer_name = os.path.basename(streamer_path)
    logging.info(f"Processing data for streamer: {streamer_name}")

    # Create output directories if they don't exist
    output_dir = os.path.join(streamer_path)
    html_dir = os.path.join(streamer_path, 'html')
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(html_dir, exist_ok=True)

    # Get all txt files in the streamer directory
    file_paths = glob.glob(os.path.join(streamer_path, '*.txt'))
    if not file_paths:
        logging.warning(f"No chat files found in {streamer_path}")
        return

    # Create the chat DataFrame first
    chat_df = concatenate_dfs(file_paths)
    chat_df['timestamp'] = pd.to_datetime(chat_df['timestamp'], format="%H:%M:%S", errors='coerce')

    # Load and process emotes for this specific streamer
    try:
        with open('emotes.json', 'r') as f:
            streamer_emotes = json.load(f)
    except Exception as e:
        logging.error(f"Error loading emotes.json: {str(e)}")
        return

    # Get emotes for this specific streamer
    emotes = streamer_emotes.get(streamer_name, [])
    if emotes:
        emote_usage = count_emote_usage(chat_df, emotes)
        sorted_emote_usage = dict(sorted(emote_usage.items(), key=lambda item: item[1], reverse=True))
        save_emote_usage_to_file(sorted_emote_usage, os.path.join(output_dir, 'emote_usage.txt'))

    # Rest of the processing...
    message_count_per_user = analyze_data(chat_df)
    top_users = message_count_per_user.head(TOP_USERS_COUNT)

    # Save visualization with streamer-specific filename
    visualize_top_users(top_users, os.path.join(output_dir, 'top_users.png'))

    # Save files in streamer-specific directory
    save_user_list_to_file(message_count_per_user, os.path.join(output_dir, 'user_message_counts.txt'))
    append_totals_to_file(message_count_per_user, os.path.join(output_dir, 'user_message_counts.txt'))

    for user in TARGET_USERS:
        count = message_count_per_user.get(user.lower(), 0)
        logging.info(f"Final count for {user}: {count}")

    # Process HTML files for this streamer
    sanitise.modify_html_files(html_dir)

def main():
    # Get all streamer directories in chattrans
    streamer_dirs = [d for d in glob.glob('chattrans/*') if os.path.isdir(d)]

    if not streamer_dirs:
        logging.warning("No streamer directories found in chattrans/")
        return

    for streamer_dir in streamer_dirs:
        process_streamer_data(streamer_dir)

if __name__ == "__main__":
    main()
