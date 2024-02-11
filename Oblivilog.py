from matplotlib.lines import lineStyles
import pandas as pd
import matplotlib.pyplot as plt
import re
import glob
import datetime

# Step 1: Parse the Data
def parse_chat_data(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            chat_data = file.readlines()
    except Exception as e:
        print(f"Error reading file {file_path}: {str(e)}")
        return pd.DataFrame(columns=['timestamp', 'username', 'message'])

    pattern = re.compile(r'\[(?P<timestamp>.+?)\] (?P<username>.+?): (?P<message>.+)')
    chat_entries = []
    for line in chat_data:
        match = pattern.match(line)
        if match:
            chat_entries.append(match.groupdict())
    
    return pd.DataFrame(chat_entries)

def concatenate_dfs(file_paths):
    dfs = []
    for file_path in file_paths:
        dfs.append(parse_chat_data(file_path))
    return pd.concat(dfs, ignore_index=True)

def analyze_data(chat_df):
    gift_phrases = ["gifted a Tier 1 sub to", "community! They've gifted a total of"]
    filtered_df = chat_df[~chat_df['message'].str.contains('|'.join(gift_phrases), case=True)]
    return filtered_df['username'].value_counts()

month_and_year = datetime.datetime.now().strftime("%B_%Y")  # Format: Month_Year
graph_filename = f"{month_and_year}.png"  # This will be something like "top_users_March_2024.png"

# Step 3: Visualize the Data
def visualize_top_users(top_users, filename):
    plt.style.use('Solarize_Light2')
    plt.figure(figsize=(18, 9))
    plt.bar(top_users.index, top_users.values, color='darkorange')
    plt.xticks(rotation=45, ha='right')
    plt.yticks(fontsize=10)
    plt.ylabel('Number of Messages')
    plt.title('Top Users by Message Count')
    plt.grid(axis='both', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(filename, dpi=300)  # Use the dynamic filename here
    plt.close()


def save_user_list_to_file(message_count, filename):
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
        print(f"Error writing to file {filename}: {str(e)}")

def count_emote_usage(chat_df, emotes):
    emote_counts = {emote: chat_df['message'].apply(lambda x: x.count(emote)).sum() for emote in emotes}
    return pd.Series(emote_counts)

def append_totals_to_file(message_count_per_user, filename):
    with open(filename, 'a', encoding='utf-8') as file:
        file.write(f"\nTotal Messages Sent: {message_count_per_user.sum()}\n")
        file.write(f"Total Participants: {len(message_count_per_user)}\n")

def save_emote_usage_to_file(emote_usage, filename):
    try:
        with open(filename, 'w', encoding='utf-8') as file:
            for emote, count in emote_usage.items():
                file.write(f"{emote}: {count}\n")
    except Exception as e:
        print(f"Error writing to file {filename}: {str(e)}")

def generate_html_file(month_and_year, graph_filename, file_count, message_count_per_user):
    with open('chat_stats.html', 'w', encoding='utf-8') as file:
        with open('user_message_counts.txt', 'r', encoding='utf-8') as user_file:
            user_list_html = user_file.read()
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Obliviosa Chatstats</title>
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Roboto&family=Roboto+Slab">
    <link rel="stylesheet" type="text/css" href="styles.css">
    <script src="https://kit.fontawesome.com/6824d55697.js" crossorigin="anonymous"></script>
</head>
<body>
    <div id="navbar-placeholder"></div>
    <h1>{month_and_year}</h1>
    <img src="{graph_filename}" alt="Chart Unavailable"/>
    <h2>Detailed chat stats</h2>
    <p>Channel VIP's are marked as <strong>bold</strong>. Mods are <em>italicised</em></p>
    <ol>
    {user_list_html}
    </ol>
    <h4><h3>{message_count_per_user.sum()}</h3>Messages sent from <h3>{len(message_count_per_user)}</h3> chat participants over <h3>{file_count}</h3> streams.</h4>
    <footer>
        <p>Go watch <a href="https://www.twitch.tv/obliviosaofficial">Obliviosa on Twitch</a> or even <a href="https://www.instagram.com/obliviosaofficial/">follow her on Instagram</a>.</p>
        <p>Statpage made with ❤️ by OfficiallySp (Shane Pepperell ©️ 2023)</p>
    </footer>
</body>
</html>"""
        file.write(html_content)

if __name__ == "__main__":
    file_paths = glob.glob('chattrans/*.txt')
    chat_df = concatenate_dfs(file_paths)
    chat_df['timestamp'] = pd.to_datetime(chat_df['timestamp'], format="%H:%M:%S", errors='coerce')

    message_count_per_user = analyze_data(chat_df)
    top_users = message_count_per_user.head(50)  # Adjust number as needed

    month_and_year_format = datetime.datetime.now().strftime("%B_%Y")  # Format: Month_Year
    graph_filename = f"{month_and_year_format}.png"  # This will be something like "top_users_March_2024.png"
    visualize_top_users(top_users, graph_filename)
    
    emotes = ["oblivi118WINK", "oblivi118Lighter", "oblivi118Hands", "oblivi118Gun",
              "oblivi118Cozy", "oblivi118Cookie", "oblivi118Lurking", "oblivi118Giggle",
              "oblivi118Sip", "oblivi118Pat", "oblivi118Sing", "oblivi118Heart",
              "oblivi118Blush", "oblivi118Huh", "oblivi118Lol", "oblivi118Hehe",
              "oblivi118What", "oblivi118Evil", "oblivi118Zzz", "oblivi118Tea"]
    emote_usage = count_emote_usage(chat_df, emotes)
    
    save_user_list_to_file(message_count_per_user, 'user_message_counts.txt')
    append_totals_to_file(message_count_per_user, 'user_message_counts.txt')
    save_emote_usage_to_file(emote_usage, 'emote_usage.txt')
    
    # Corrected call to generate_html_file with all required arguments
    generate_html_file(datetime.datetime.now().strftime("%B %Y"), graph_filename, len(file_paths), message_count_per_user)