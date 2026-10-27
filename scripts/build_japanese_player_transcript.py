"""Build Japanese timed transcripts for the shared podcast player.

The display text comes from the checked Japanese/English parallel script. Whisper cue
times are aligned to that script by character sequence; cue text itself is never shown.
"""
import argparse
import difflib
import hashlib
import json
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT.parent / "macro102" / "publishing" / "spotify" / "japanese"
EPISODE_ID = "podcast-ja-ch{chapter:02}-macroeconomics"


def normalized(text):
    text = unicodedata.normalize("NFKC", text).casefold()
    # These product names are read aloud in Japanese although the script keeps
    # their Latin spelling. Normalize the common ASR renderings to the script form.
    for spoken, written in (("コラボ", "colab"), ("モデルアプリ", "modelapps"),
                            ("データアプリ", "dataapps"), ("ショー", "章"),
                            ("とおり", "通り"), ("算出量", "産出量"),
                            ("低減", "逓減"), ("喧嘩焼却", "減価償却")):
        text = text.replace(spoken, written)
    return "".join(c for c in text if not c.isspace() and unicodedata.category(c)[0] not in "PZ")


def build(source, chapter):
    prefix = f"chapter-{chapter:02}"
    chunks_path = source / f"evidence/{prefix}-chunks.json"
    cues_path = source / f"transcripts/{prefix}.asr-draft.json"
    parallel_path = source / f"transcripts/{prefix}.parallel.json"
    chunks_doc = json.loads(chunks_path.read_text())
    cues_doc = json.loads(cues_path.read_text())
    parallel_doc = json.loads(parallel_path.read_text())
    audio_hash = chunks_doc["audio_sha256"]
    if cues_doc["audio_sha256"] != audio_hash:
        raise ValueError("ASR cue data belongs to a different audio file")
    if cues_doc["duration_seconds"] != chunks_doc["duration_seconds"]:
        raise ValueError("Transcript and chunk manifest durations differ")
    parallel = {item["id"]: item for item in parallel_doc["passages"]}

    segments = []
    sections = []
    previous_end = 0.0
    for chunk in chunks_doc["chunks"]:
        turns = chunk["turns"]
        cues = [cue for cue in cues_doc["cues"] if cue["chunk"] == chunk["index"]]
        target_parts = []
        target_ranges = []
        target_offset = 0
        for turn in turns:
            passage = parallel.get(turn["id"])
            if not passage or passage["ja"] != turn["text"]:
                raise ValueError(f"Parallel script mismatch for {turn['id']}")
            part = normalized(turn["text"])
            if not part:
                raise ValueError(f"Empty normalized transcript for {turn['id']}")
            target_ranges.append((target_offset, target_offset + len(part)))
            target_parts.append(part)
            target_offset += len(part)
        target = "".join(target_parts)

        cue_positions = []
        observed_parts = []
        observed_offset = 0
        for cue in cues:
            part = normalized(cue["text"])
            if not part:
                continue
            observed_parts.append(part)
            span = cue["end"] - cue["start"]
            for index in range(len(part)):
                cue_positions.append((
                    cue["start"] + span * index / len(part),
                    cue["start"] + span * (index + 1) / len(part),
                ))
            observed_offset += len(part)
        observed = "".join(observed_parts)
        matcher = difflib.SequenceMatcher(None, target, observed, autojunk=False)
        if matcher.ratio() < 0.90:
            raise ValueError(f"ASR/script alignment below 90% in chunk {chunk['index']}: {matcher.ratio():.3f}")
        target_to_observed = {}
        for target_start, observed_start, length in matcher.get_matching_blocks():
            for offset in range(length):
                target_to_observed[target_start + offset] = observed_start + offset

        for turn, (start_offset, end_offset) in zip(turns, target_ranges):
            matched = [
                cue_positions[target_to_observed[pos]]
                for pos in range(start_offset, end_offset)
                if pos in target_to_observed
            ]
            if len(matched) < (end_offset - start_offset) * 0.75:
                # A main ASR pass can skip a short turn even when the audio contains it.
                # Use saved overlapping-window ASR as timing evidence for that turn.
                work = source.parents[2] / ".work" / "podcast-japanese" / prefix
                pcm_name = Path(chunk["pcm"]).stem
                chunk_hash = pcm_name.split("-")[-1]
                for window_path in sorted(work.glob(f"asr-{chunk_hash[:16]}-w*.json")):
                    window_text = window_path.stem.rsplit("-w", 1)[-1]
                    try:
                        window_start = int(window_text)
                    except ValueError:
                        continue
                    window = json.loads(window_path.read_text())
                    window_positions = []
                    window_parts = []
                    for cue in window.get("transcription", []):
                        part = normalized(cue.get("text", ""))
                        if not part:
                            continue
                        cue_start = cue["offsets"]["from"] / 1000
                        cue_end = cue["offsets"]["to"] / 1000
                        span = cue_end - cue_start
                        window_parts.append(part)
                        window_positions.extend((
                            chunk["start_seconds"] + window_start + cue_start + span * i / len(part),
                            chunk["start_seconds"] + window_start + cue_start + span * (i + 1) / len(part),
                        ) for i in range(len(part)))
                    window_observed = "".join(window_parts)
                    window_matcher = difflib.SequenceMatcher(None, normalized(turn["text"]), window_observed, autojunk=False)
                    window_coverage = sum(block.size for block in window_matcher.get_matching_blocks()) / max(len(normalized(turn["text"])), 1)
                    window_map = {}
                    for target_pos, observed_pos, length in window_matcher.get_matching_blocks():
                        for offset in range(length):
                            window_map[target_pos + offset] = observed_pos + offset
                    window_matched = [window_positions[window_map[pos]] for pos in range(len(normalized(turn["text"]))) if pos in window_map]
                    if (window_coverage >= 0.75 and
                            len(window_matched) >= len(normalized(turn["text"])) * 0.75):
                        matched = window_matched
                        break
            if len(matched) < (end_offset - start_offset) * 0.75:
                raise ValueError(f"Insufficient timing alignment for {turn['id']}")
            start = min(span[0] for span in matched)
            end = max(span[1] for span in matched)
            # ASR can place the first cue a few tenths of a second after the
            # audio begins. The player timeline must start at zero, so include
            # that short leading interval with the first spoken passage.
            if not segments and start <= 0.5:
                start = 0.0
            start = max(start, previous_end)
            end = max(end, start + 0.05)
            if end > chunks_doc["duration_seconds"]:
                raise ValueError(f"Transcript timing exceeds audio duration at {turn['id']}")
            if not segments or sections[-1]["title"] != chunk["section"]:
                sections.append({"title": chunk["section"], "start": start, "segment": len(segments)})
            segments.append({
                "start": round(start, 3),
                "end": round(end, 3),
                "speaker": "司会者" if turn["speaker"] == "HOST" else "経済学者",
                "text": turn["text"],
                "id": turn["id"],
            })
            previous_end = end

    if not segments or sections[0]["start"] != 0:
        raise ValueError("First timed passage must begin at zero")
    document = {
        "title": f"第{chapter}章 · " + next(
            item["title"].split("：", 1)[-1]
            for item in json.loads((source / "series-metadata.ja.json").read_text())["chapters"]
            if item["number"] == chapter
        ),
        "duration": chunks_doc["duration_seconds"],
        "sections": sections,
        "segments": segments,
        "audio_sha256": audio_hash,
        "script_sha256": hashlib.sha256(parallel_path.read_bytes()).hexdigest(),
        "timing_method": "Whisper large-v3-turbo cue boundaries aligned to the verified Japanese script by character sequence; passage timing is approximate.",
    }
    return document


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--chapter", type=int, choices=range(1, 22), default=1)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = build(args.source_dir, args.chapter)
    output = args.output or ROOT / f"transcript-inputs-ja/podcast-ja-ch{args.chapter:02}-macroeconomics.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(f"Wrote {len(result['segments'])} aligned passages across {len(result['sections'])} sections.")


if __name__ == "__main__":
    main()
