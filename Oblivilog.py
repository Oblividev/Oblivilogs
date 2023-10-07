import pandas as pd
import matplotlib.pyplot as plt
import re
import glob

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
    return chat_df['username'].value_counts()

# Step 3: Visualize the Data
def visualize_top_users(top_users):
    plt.figure(figsize=(12, 7))
    plt.bar(top_users.index, top_users.values, color='skyblue')
    plt.xticks(rotation=45, ha='right')
    plt.ylabel('Number of Messages')
    plt.title('Top Users by Message Count')
    plt.tight_layout()
    plt.show()

def save_user_list_to_file(message_count, filename):
    try:
        with open(filename, 'w', encoding='utf-8') as file:
            prev_count = -1
            shared_rank = 1
            for rank, (user, count) in enumerate(message_count.items(), start=1):
                # Check if this user shares a rank with the previous user(s)
                if count == prev_count:
                    rank = shared_rank  # Use the rank of the first user with this count
                else:
                    shared_rank = rank  # Update the shared rank
                file.write(f"{rank}. {user}: {count} messages\n")
                prev_count = count  # Update the count to check against for the next user
    except Exception as e:
        print(f"Error writing to file {filename}: {str(e)}")

def plot_messages_over_time(chat_df):
    chat_df.set_index('timestamp', inplace=True)
    messages_over_time = chat_df.resample('T').size() # 'T' for minute intervals
    plt.figure(figsize=(12, 7))
    plt.plot(messages_over_time.index, messages_over_time.values, color='skyblue')
    plt.title('Messages Over Time')
    plt.xlabel('Time')
    plt.ylabel('Number of Messages')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def count_emote_usage(chat_df, emotes):
    emote_counts = {emote: chat_df['message'].apply(lambda x: x.count(emote)).sum() for emote in emotes}
    return pd.Series(emote_counts)

def append_totals_to_file(message_count_per_user, filename):
    with open(filename, 'a', encoding='utf-8') as file:
        file.write(f"\nTotal Messages Sent: {message_count_per_user.sum()}\n")
        file.write(f"Total Participants: {len(message_count_per_user)}\n")

# Main Execution
if __name__ == "__main__":
    file_paths = glob.glob('chattrans/*.txt')
    chat_df = concatenate_dfs(file_paths)
    
    # Ensure that your timestamp format matches the actual format in your data
    chat_df['timestamp'] = pd.to_datetime(chat_df['timestamp'], errors='coerce')

    message_count_per_user = analyze_data(chat_df)
    top_users = message_count_per_user.head(50)
    
    visualize_top_users(top_users)
    plot_messages_over_time(chat_df)
    
    # Emote Usage
    emotes = ["oblivi118WINK", "oblivi118Lighter", "oblivi118Hands", "oblivi118Gun",
              "oblivi118Cozy", "oblivi118Cookie", "oblivi118Lurking", "oblivi118Giggle",
              "oblivi118Sip", "oblivi118Pat", "oblivi118Sing", "oblivi118Heart",
              "oblivi118Blush", "oblivi118Huh", "oblivi118Lol", "oblivi118Hehe",
              "oblivi118What", "oblivi118Evil", "oblivi118Zzz"]
    emote_usage = count_emote_usage(chat_df, emotes)
    print("Emote Usage:")
    print(emote_usage)
    
    save_user_list_to_file(message_count_per_user, 'user_message_counts.txt')
    append_totals_to_file(message_count_per_user, 'user_message_counts.txt')