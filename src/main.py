import math
import os

import context_reader
import executor
import transcript_processor as tp
import utility as util
from src import report_selection


def get_chunk_size(transcript_segments, max_caption_number):
    total_captions = len(transcript_segments)
    chunk_num = math.ceil(total_captions / max_caption_number)
    last_len = total_captions % max_caption_number

    final_len = max_caption_number
    if chunk_num > 1 and last_len < max_caption_number/3:
        padding = math.ceil(last_len / (chunk_num - 1))
        final_len += padding

    return final_len


def get_caption_chunks(transcript_segments, max_caption_number):
    chunks = []
    chunk = ""
    iterate = 0
    ideal_caption_number = get_chunk_size(transcript_segments, max_caption_number)
    for segment in transcript_segments:
        chunk += f"\n{str(segment)}\n"
        iterate += 1

        if iterate > ideal_caption_number:
            chunks.append(chunk)
            chunk = f"\n{str(segment)}\n"
            iterate = 0
    if len(chunk) > 0:
        chunks.append(chunk)

    return chunks


def remove_last_blank_line(s):
    lines = s.split('\n')

    # Check if the last line is blank and remove it if so
    if lines and lines[-1].strip() == '':
        lines.pop()

    return '\n'.join(lines)


def run_reca11():
    projects = ['money manager', 'goose sighting', 'fable']
    chunk_num = 100

    for project in projects:
        directory = os.path.join('../artifacts/transcripts', project)

        for file in sorted(os.listdir(directory)):

            filepath = os.path.join(directory, file)

            transcript_segments = tp.extract_segments_from_transcript(filepath)
            caption_chunks = get_caption_chunks(transcript_segments, chunk_num)

            print(f"{project} > {file}")

            reports = {}
            for i in range(1):
                context_string = context_reader.get_all_context_string(project, file)
                print(context_string)

                all_result_strs = ""
                total_tokens = 0
                current_report = []

                for iteration, chunk in enumerate(caption_chunks):
                    token_count, result = executor.run_model(chunk, context_string)
                    current_report.extend(result)
                    total_tokens += token_count

                reports[i+1] = current_report

            report_selection.run_report_selection(reports)
            break
        break


if __name__ == '__main__':
    run_reca11()
