#!/usr/bin/env python3
"""
Validate shortener domains from PeterDaveHello list.
Checks if domains actually resolve and respond to HTTP requests.
"""
import subprocess, json, sys, time, concurrent.futures

def check_domain(domain):
    """Check if a domain is alive and looks like a shortener"""
    url = f"https://{domain}"
    try:
        r = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "--max-time", "8",
             url, "-H", "User-Agent: Mozilla/5.0"],
            capture_output=True, text=True, timeout=10
        )
        code = r.stdout.strip()
        if code and code not in ["000", "502", "503", "504", "403"]:
            return (domain, code, "alive")
        return (domain, code, "dead")
    except:
        return (domain, "timeout", "dead")

def main():
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    list_path = os.path.join(script_dir, "shorteners.txt")

    with open(list_path) as f:
        domains = [l.strip().lower() for l in f if l.strip() and not l.startswith("#")]

    print(f"Total domains to check: {len(domains)}", file=sys.stderr)

    alive = []
    dead = []
    checked = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(check_domain, d): d for d in domains}
        for future in concurrent.futures.as_completed(futures):
            domain, code, status = future.result()
            checked += 1
            if status == "alive":
                alive.append((domain, code))
            else:
                dead.append((domain, code))
            if checked % 100 == 0:
                print(f"[{checked}/{len(domains)}] alive: {len(alive)} dead: {len(dead)}", file=sys.stderr)
            time.sleep(0.05)  # rate limit

    alive.sort()
    dead.sort()

    # Write results
    with open(os.path.join(script_dir, "shorteners_alive.txt"), "w") as f:
        f.write(f"# Alive shortener domains ({len(alive)})\n")
        f.write(f"# Checked: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        for d, c in alive:
            f.write(f"{d}\n")

    with open(os.path.join(script_dir, "shorteners_dead.txt"), "w") as f:
        f.write(f"# Dead/unreachable shortener domains ({len(dead)})\n")
        f.write(f"# Checked: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        for d, c in dead:
            f.write(f"{d} (HTTP {c})\n")

    print(f"\n=== Results ===", file=sys.stderr)
    print(f"Total:    {len(domains)}", file=sys.stderr)
    print(f"Alive:    {len(alive)}", file=sys.stderr)
    print(f"Dead:     {len(dead)}", file=sys.stderr)
    print(f"Rate:     {len(alive)/len(domains)*100:.1f}% alive", file=sys.stderr)

if __name__ == "__main__":
    main()
