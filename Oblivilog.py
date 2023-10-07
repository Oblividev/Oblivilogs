import pandas as pd
import matplotlib.pyplot as plt
import re
import glob  # To get file paths

# Step 1: Parse the Data
def parse_chat_data(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        chat_data = file.readlines()
    
    pattern = re.compile(r'\[(?P<timestamp>.+?)\] (?P<username>.+?): (?P<message>.+)')
    chat_entries = []
    for line in chat_data:
        match = pattern.match(line)
        if match:
            chat_entries.append(match.groupdict())
    
    return pd.DataFrame(chat_entries)

# Use glob to get all file paths, assuming all chat logs are in 'chat_logs/' directory and have '.txt' extension
file_paths = glob.glob('chattrans/*.txt')
dfs = []
for file_path in file_paths:
    dfs.append(parse_chat_data(file_path))

# Concatenate all the DataFrames into one
chat_df = pd.concat(dfs, ignore_index=True)

# Step 2: Analyze the Data
message_count_per_user = chat_df['username'].value_counts()

# Step 3: Visualize the Data
top_users = message_count_per_user.head(25)  # Adjust number as per requirement

plt.figure(figsize=(12, 7))
plt.bar(top_users.index, top_users.values, color='skyblue')
plt.xticks(rotation=45, ha='right')
plt.ylabel('Number of Messages')
plt.title('Top Users by Message Count')
plt.tight_layout()
plt.show()

