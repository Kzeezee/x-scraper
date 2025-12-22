import aiohttp
import asyncio
import os
import mimetypes # Import mimetypes to guess extension from content type
from typing import List, Tuple
from urllib.parse import urlparse

async def download_media(media_urls: List[str], output_dir: str) -> List[Tuple[str, str]]:
    """
    Downloads a list of media URLs concurrently, determining file extension from Content-Type.

    Args:
        media_urls: A list of URLs to download.
        output_dir: The directory to save the downloaded media.

    Returns:
        A list of tuples, where each tuple contains (original_url, saved_path).
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    async def _fetch(session, url: str, base_filename: str):
        try:
            async with session.get(url) as response:
                response.raise_for_status()
                
                content_type = response.headers.get("Content-Type")
                if not content_type:
                    print(f"Warning: No Content-Type header for {url}. Cannot determine file extension.")
                    return url, None

                # Guess the extension. Add fallback for common types if needed.
                ext = mimetypes.guess_extension(content_type.split(';')[0].strip())
                if ext == '.jpe': ext = '.jpg' # Common correction
                
                if not ext:
                    print(f"Warning: Could not determine extension for Content-Type '{content_type}' from {url}.")
                    # Fallback to parsing the URL as a last resort
                    parsed_url = urlparse(url)
                    url_path = parsed_url.path
                    _, url_ext = os.path.splitext(url_path)
                    if url_ext:
                        ext = url_ext
                    else:
                        # Final fallback if still no extension
                        return url, None

                final_filename = f"{base_filename}{ext}"
                final_filepath = os.path.join(output_dir, final_filename)

                with open(final_filepath, 'wb') as f:
                    while True:
                        chunk = await response.content.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)
                
                return url, final_filepath

        except aiohttp.ClientError as e:
            print(f"Error downloading {url}: {e}")
            return url, None
        except Exception as e:
            print(f"An unexpected error occurred for {url}: {e}")
            return url, None

    saved_files = []
    async with aiohttp.ClientSession() as session:
        tasks = []
        for url in media_urls:
            # Generate a base filename from the URL path, removing query params
            base_filename = os.path.basename(urlparse(url).path)
            tasks.append(_fetch(session, url, base_filename))
        
        results = await asyncio.gather(*tasks)
        for original_url, saved_path in results:
            if saved_path:
                saved_files.append((original_url, saved_path))
    
    return saved_files

if __name__ == "__main__":
    # Example Usage:
    async def run_example():
        output_dir = "output_media_test"
        # Example URLs from Twitter with different formats
        test_urls = [
            "https://pbs.twimg.com/media/GA-KyxEWkAA49aC?format=jpg&name=large",
            "https://pbs.twimg.com/ext_tw_video_thumb/1732544832757256192/pu/img/lI92aXz-46gA_8A-?format=jpg&name=small"
        ]
        print(f"Starting download test, saving to '{output_dir}'...")
        results = await download_media(test_urls, output_dir)
        print("Download test finished.")
        for original, saved in results:
            print(f"  - Original: {original}")
            print(f"    Saved to: {saved}")
            
    asyncio.run(run_example())
