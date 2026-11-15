"""Run the CrewAI 5-Agent Kurra MVP Team."""
import json
import os
import sys
from pathlib import Path

# Load environment variables from .env if present
env_file = Path(__file__).resolve().parent / ".env"
if env_file.exists():
    for line in env_file.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip("'\""))

os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"
os.environ["OTEL_SDK_DISABLED"] = "true"

from kurra.crew import create_kurra_crew

def main():
    print("=" * 70)
    print("🚀 Launching Kurra Multi-Agent Team (CrewAI 1.9.3 + Gemini 3.8 Flash)")
    print("=" * 70)
    
    crew = create_kurra_crew()
    if crew is None:
        print("ERROR: Failed to create CrewAI team.")
        sys.exit(1)
        
    result = crew.kickoff()
    
    print("\n" + "=" * 70)
    print("🎉 CREW EXECUTION COMPLETE")
    print("=" * 70)
    print(result)
    
    # Save output
    output_path = Path("data/crew_execution_result.md")
    output_path.write_text(str(result), encoding="utf-8")
    print(f"\n[Saved result to {output_path}]")

if __name__ == "__main__":
    main()
