"""prompt_size.py: measure the SQL prompt (decision E-13: measured and recorded, never cut).

Run:  python scripts/prompt_size.py
The token figure is an estimate (characters / 4). The exact count for each model is
printed by scripts/smoke_test.py and scripts/speed_check.py ("tokens read").
"""
from emole.pipeline import prompts


def main():
    s = prompts.prompt_size()
    print(f"SQL prompt {s['version']}: {s['messages']} messages, {s['characters']:,} characters, "
          f"about {s['estimated_tokens']:,} tokens, {s['examples']} worked examples")


if __name__ == "__main__":
    main()
