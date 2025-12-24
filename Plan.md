# Plan for new 'select' feature

1.  **CLI Interface (`main.py`):**
    *   Add a new subcommand `select` to the argument parser.
    *   The `select` subcommand will have the following arguments:
        *   `--input-dir`: Path to the directory containing `tweets.jsonl` and `media` folder. (Required)
        *   `--output-dir`: Path to the directory where the selected data will be saved. (Required)
        *   `--min-replies`: Minimum number of replies. (Default: 0)
        *   `--min-reposts`: Minimum number of reposts. (Default: 0)
        *   `--min-likes`: Minimum number of likes. (Default: 0)
        *   `--min-bookmarks`: Minimum number of bookmarks. (Default: 0)
        *   `--min-views`: Minimum number of views. (Default: 0)
        *   `--sort-by`: How to sort the output `tweets.jsonl`. Options: `likes`, `views`. (Default: `views`)
        *   `--action`: Whether to `copy` or `move` media files. Options: `copy`, `move`. (Default: `copy`)

2.  **Selection Logic (`selector.py`):**
    *   Create a new file `selector.py`.
    *   Implement a function `select_tweets` that takes the parsed arguments as input.
    *   This function will:
        *   Read the `tweets.jsonl` file from the `input-dir`.
        *   Iterate through each tweet and check if it meets the filter criteria (`min-replies`, `min-reposts`, etc.).
        *   Store the matching tweets in a list.
        *   Sort the list of matching tweets based on the `sort-by` argument.
        *   Create the `output-dir` if it doesn't exist.
        *   Create a `selected` folder inside the `output-dir` for media.
        *   Write the sorted list of tweets to a new `tweets.jsonl` file in the `output-dir`.
        *   For each selected tweet, find the corresponding media in the `input-dir/media` folder.
        *   Based on the `action` argument, either copy or move the media files to `output-dir/selected`.

3.  **Integration:**
    *   In `main.py`, call the `select_tweets` function from `selector.py` when the `select` subcommand is used.
    *   Pass the parsed arguments to the function.

4.  **Testing:**
    *   Create a sample directory with `tweets.jsonl` and a `media` folder to test the functionality.
    *   Run the `select` command with different options to verify:
        *   Correct filtering.
        *   Correct sorting.
        *   Correct file operations (`copy`/`move`).
        *   Correct output structure.
