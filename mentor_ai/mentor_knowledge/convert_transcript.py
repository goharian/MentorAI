import json
import re

def text_to_transcript(text_file, output_file):
    with open(text_file, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # split text into sentences
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    # create transcript
    transcript = []
    current_time = 0.0
    
    for sentence in sentences:
        # calculate duration based on sentence length
        words = len(sentence.split())
        duration = max(2.0, words * 0.3)  # ~0.3 seconds per word, min 2 seconds
        
        transcript.append({
            "text": sentence,
            "start": round(current_time, 2),
            "duration": round(duration, 2)
        })
        current_time += duration
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(transcript, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Created {output_file} with {len(transcript)} segments")
    print(f"✓ Total duration: {current_time:.0f} seconds (~{current_time/60:.1f} minutes)")

text_to_transcript('..\\NoteGPT_TRANSCRIPT_1767706641907.txt', 'transcript.json')