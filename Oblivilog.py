from matplotlib.lines import lineStyles
import sanitise
import pandas as pd
import matplotlib.pyplot as plt
import re
import glob
import logging
from typing import List, Dict

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
            chat_entries.append(match.groupdict())
    
    return pd.DataFrame(chat_entries)

def concatenate_dfs(file_paths: List[str]) -> pd.DataFrame:
    dfs = []
    for file_path in file_paths:
        dfs.append(parse_chat_data(file_path))
    return pd.concat(dfs, ignore_index=True)

def analyze_data(chat_df: pd.DataFrame) -> pd.Series:
    gift_phrases = ["gifted a Tier 1 sub to", "They've gifted a total of"]
    filtered_df = chat_df[~chat_df['message'].str.contains('|'.join(gift_phrases), case=True)]
    return filtered_df['username'].value_counts()

def visualize_top_users(top_users: pd.Series):
    plt.style.use('Solarize_Light2')
    plt.figure(figsize=(18, 9))
    plt.bar(top_users.index, top_users.values, color='darkorange')
    plt.xticks(rotation=45, ha='right')
    plt.yticks(fontsize=10)
    plt.ylabel('Number of Messages')
    plt.title('Top Users by Message Count')
    plt.grid(axis='both', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig('top_users.png', dpi=300)
    plt.close()

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
        with open(filename, 'w', encoding='utf-8') as file:
            for emote, count in emote_usage.items():
                file.write(f"{emote}: {count}\n")
    except Exception as e:
        logging.error(f"Error writing to file {filename}: {str(e)}")

def main():
    file_paths = glob.glob('chattrans/*.txt')
    chat_df = concatenate_dfs(file_paths)
    
    chat_df['timestamp'] = pd.to_datetime(chat_df['timestamp'], format="%H:%M:%S", errors='coerce')

    message_count_per_user = analyze_data(chat_df)
    top_users = message_count_per_user.head(TOP_USERS_COUNT)
    
    visualize_top_users(top_users)
    
    emotes = ["oblivi118WINK", "oblivi118Lighter", "oblivi118Hands", "oblivi118Gun",
              "oblivi118Cozy", "oblivi118Cookie", "oblivi118Lurking", "oblivi118Giggle",
              "oblivi118Sip", "oblivi118Pat", "oblivi118Sing", "oblivi118Heart",
              "oblivi118Blush", "oblivi118Huh", "oblivi118Lol", "oblivi118Hehe",
              "oblivi118What", "oblivi118Evil", "oblivi118Zzz", "oblivi118Tea"]
    emote_usage = count_emote_usage(chat_df, emotes)
    logging.info("Emote Usage:")
    logging.info(emote_usage)
    
    save_user_list_to_file(message_count_per_user, 'user_message_counts.txt')
    append_totals_to_file(message_count_per_user, 'user_message_counts.txt')
    
    sorted_emote_usage = dict(sorted(emote_usage.items(), key=lambda item: item[1], reverse=True))
    save_emote_usage_to_file(sorted_emote_usage, 'emote_usage.txt')
    
    for user in TARGET_USERS:
        count = message_count_per_user.get(user.lower(), 0)
        logging.info(f"Final count for {user}: {count}")
    
    sanitise.modify_html_files()

if __name__ == "__main__":
    main()

