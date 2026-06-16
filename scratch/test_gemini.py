import os
import asyncio
from google import genai
from google.genai import types

async def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    
    files = []
    for f in client.files.list():
        if f.state == "ACTIVE":
            files.append(f)
            if len(files) == 2:
                break
                
    if not files:
        print("No files")
        return
        
    print(f"File 0 MIME: {files[0].mime_type}, URI: {files[0].uri}")
    
    # Test 1: using the File object directly
    try:
        print("Testing with File object...")
        contents = [files[0], "Describe this video."]
        res = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents
        )
        print("File object success:", res.text[:50])
    except Exception as e:
        print(f"File object failed: {e}")
        
    # Test 2: using Part.from_uri with correct MIME type
    try:
        print("Testing with Part.from_uri and correct mime...")
        contents = [types.Part.from_uri(file_uri=files[0].uri, mime_type=files[0].mime_type), "Describe this video."]
        res = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents
        )
        print("Part.from_uri success:", res.text[:50])
    except Exception as e:
        print(f"Part.from_uri failed: {e}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), '../backend/.env'))
    asyncio.run(main())
