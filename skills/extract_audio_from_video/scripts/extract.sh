#!/bin/bash
input_dir="$1"
output_dir="$2"
mkdir -p "$output_dir"

while true; do
    batch=0
    for f in "$input_dir"/*.mp4; do
        output="${output_dir}/$(basename "${f%.mp4}.mp3")"
        if [ ! -f "$output" ]; then
            ffmpeg -i "$f" -vn -acodec libmp3lame -q:a 2 "$output" -y 2>/dev/null
            batch=$((batch + 1))
        fi
    done
    [ $batch -eq 0 ] && break
done

done_count=$(ls "$output_dir"/*.mp3 2>/dev/null | wc -l)
total_count=$(ls "$input_dir"/*.mp4 2>/dev/null | wc -l)
echo "Done: $done_count/$total_count audio files extracted."
