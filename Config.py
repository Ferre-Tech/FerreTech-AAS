from Resources.config_tool import config_tool
from Resources.constants import VERSION

def main():
    print(f"FerreTech Auto-Arousal system config tool v{VERSION}\n")
    print("Paste in an avatar ID and hit enter:")
    e = input()
    config_tool(e)

#If ran by itself, run the main loop with the supplied input
try:
    main()    
except KeyboardInterrupt:
    print("Exiting...")
    raise SystemExit(0)