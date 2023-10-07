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

# Main Execution
if __name__ == "__main__":
    file_paths = glob.glob('chattrans/*.txt')
    chat_df = concatenate_dfs(file_paths)
    
    # Optionally: Parse 'timestamp' to datetime object for further analysis
    chat_df['timestamp'] = pd.to_datetime(chat_df['timestamp'], errors='coerce')

    message_count_per_user = analyze_data(chat_df)
    top_users = message_count_per_user.head(25)  # Adjust number as per requirement
    
    visualize_top_users(top_users)