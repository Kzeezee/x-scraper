import os
import json
import shutil

async def run_selector(args):
    """Selects and filters tweets based on specified criteria."""
    input_jsonl_path = os.path.join(args.input_dir, "tweets.jsonl")
    if not os.path.exists(input_jsonl_path):
        print(f"Error: {input_jsonl_path} not found.")
        return

    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    output_jsonl_path = os.path.join(args.output_dir, "tweets.jsonl")
    output_media_path = os.path.join(args.output_dir, "selected")

    if not os.path.exists(output_media_path):
        os.makedirs(output_media_path)

    selected_tweets = []
    with open(input_jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                tweet = json.loads(line)
                if (tweet.get("reply_count", 0) >= args.min_replies and
                    tweet.get("repost_count", 0) >= args.min_reposts and
                    tweet.get("like_count", 0) >= args.min_likes and
                    tweet.get("bookmark_count", 0) >= args.min_bookmarks and
                    tweet.get("view_count", 0) >= args.min_views):
                    selected_tweets.append(tweet)
            except json.JSONDecodeError:
                print(f"Skipping invalid line in {input_jsonl_path}")

    sort_key = "like_count" if args.sort_by == "likes" else "view_count"
    selected_tweets.sort(key=lambda t: t.get(sort_key, 0), reverse=True)

    with open(output_jsonl_path, "w", encoding="utf-8") as f:
        for tweet in selected_tweets:
            f.write(json.dumps(tweet, ensure_ascii=False) + "\n")

    input_media_path = os.path.join(args.input_dir, "media")
    for tweet in selected_tweets:
        for media_path in tweet.get("media_local_paths", []):
            if media_path:
                base_filename = os.path.basename(media_path)
                src_media_path = os.path.join(input_media_path, base_filename)
                dest_media_path = os.path.join(output_media_path, base_filename)
                
                if os.path.exists(src_media_path):
                    if args.action == "copy":
                        shutil.copy(src_media_path, dest_media_path)
                    elif args.action == "move":
                        shutil.move(src_media_path, dest_media_path)

    print(f"Selected {len(selected_tweets)} tweets.")
    print(f"Selected tweets saved to {output_jsonl_path}")
    print(f"Media files saved to {output_media_path}")
