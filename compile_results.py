
import json
import os

def compile_jsonl_results(root_dir, output_file):
    """
    Compiles all tweets.jsonl files from subdirectories into a single JSON file.

    Args:
        root_dir (str): The root directory containing the scraped data subdirectories.
        output_file (str): The path to the output JSON file.
    """
    all_data = []
    for dir_name in os.listdir(root_dir):
        dir_path = os.path.join(root_dir, dir_name)
        if os.path.isdir(dir_path):
            jsonl_path = os.path.join(dir_path, 'tweets.jsonl')
            if os.path.exists(jsonl_path):
                print(f"Processing {jsonl_path}...")
                with open(jsonl_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            all_data.append(json.loads(line))
                        except json.JSONDecodeError:
                            print(f"Skipping invalid JSON line in {jsonl_path}")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)
    print(f"\nSuccessfully compiled all tweets into {output_file}")

if __name__ == '__main__':
    # The user wants to compile the results from each subdirectory in 
    # /run/media/kez/T9/x-scraped-data/{some_dir}/tweets.jsonl 
    # into a single json file.
    scraped_data_dir = '/run/media/kez/T9/x-scraped-data'
    output_json_file = 'compiled_tweets.json'
    compile_jsonl_results(scraped_data_dir, output_json_file)
