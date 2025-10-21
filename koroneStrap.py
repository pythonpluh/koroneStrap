import os
import subprocess
import sys
import json
import platform
import glob
import urllib.request
import urllib.error
from colorama import Fore, Style, init

init(autoreset=True)

FASTFLAGS_FILE = "fastFlags.json"
BOOTSTRAPPER_URL = "https://setup.pekora.zip/PekoraPlayerLauncher.exe"
BOOTSTRAPPER_FILE = "PekoraPlayerLauncher.exe"

if os.name == "nt":
    import msvcrt
    def press_any_key(prompt="Press any key to continue..."):
        print(Fore.MAGENTA + prompt, end="", flush=True)
        msvcrt.getch()
        print()
else:
    def press_any_key(prompt="Press any key to continue..."):
        input(Fore.MAGENTA + prompt)

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def get_system_info():
    system = platform.system().lower()
    return {
        'is_windows': system == 'windows',
        'is_linux': system == 'linux',
        'is_macos': system == 'darwin',
        'system_name': system
    }

def get_version_roots():
    sys_info = get_system_info()
    roots = []
    if sys_info['is_windows']:
        roots.extend([
            os.path.expandvars(r"%localappdata%\ProjectX\Versions"),
            os.path.expandvars(r"%localappdata%\Pekora\Versions"),
        ])
    elif sys_info['is_linux']:
        user = os.getenv('USER', 'user')
        roots.extend([
            os.path.expanduser(f"~/.wine/drive_c/users/{user}/AppData/Local/ProjectX/Versions"),
            os.path.expanduser(f"~/.wine/drive_c/users/{user}/AppData/Local/Pekora/Versions"),
            os.path.expanduser(f"~/.local/share/wineprefixes/pekora/drive_c/users/{user}/AppData/Local/Pekora/Versions"),
            os.path.expanduser(f"~/.local/share/wineprefixes/projectx/drive_c/users/{user}/AppData/Local/ProjectX/Versions"),
        ])
    elif sys_info['is_macos']:
        # please work pleaase work please work
        roots.extend([
            "/Users/alex/.wine/drive_c/users/alex/AppData/Local/ProjectX/Versions",
            "/Users/alex/.wine/drive_c/users/alex/AppData/Local/Pekora/Versions",
        ])
        roots.extend(glob.glob(os.path.expanduser(f"~/Library/Application Support/CrossOver/Bottles/*/drive_c/users/{user}/AppData/Local/ProjectX/Versions")))
        roots.extend(glob.glob(os.path.expanduser(f"~/Library/Application Support/CrossOver/Bottles/*/drive_c/users/{user}/AppData/Local/Pekora/Versions")))
    return [p for p in roots if isinstance(p, str)]

def iter_version_dirs():
    for root in get_version_roots():
        if os.path.isdir(root):
            for d in sorted(glob.glob(os.path.join(root, "*"))):
                if os.path.isdir(d):
                    yield d

def get_clientsettings_targets():
    targets = []
    for ver in iter_version_dirs():
        for folder in ["2020L", "2021M"]:
            folder_path = os.path.join(ver, folder)
            if os.path.isdir(folder_path):
                client_dir = os.path.join(folder_path, "ClientSettings")
                settings_path = os.path.join(client_dir, "ClientAppSettings.json")
                targets.append((client_dir, settings_path, folder))
    return targets

def get_executable_paths(folder):
    paths = []
    for ver in iter_version_dirs():
        exe = os.path.join(ver, folder, "ProjectXPlayerBeta.exe")
        paths.append(exe)
    return paths

def load_fastflags():
    if not os.path.exists(FASTFLAGS_FILE):
        with open(FASTFLAGS_FILE, "w") as f:
            json.dump({}, f)
        return {}
    try:
        with open(FASTFLAGS_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(Fore.RED + "[!] Error reading fastFlags.json - invalid JSON format")
        return {}

def save_fastflags(fastflags):
    try:
        with open(FASTFLAGS_FILE, "w") as f:
            json.dump(fastflags, f, indent=2)
        print(Fore.GREEN + "[*] FastFlags saved successfully!")
    except Exception as e:
        print(Fore.RED + f"[!] Failed to save FastFlags: {e}")

def apply_fastflags(fastflags):
    success = False
    for client_dir, settings_path, folder in get_clientsettings_targets():
        try:
            os.makedirs(client_dir, exist_ok=True)
            if os.path.exists(settings_path):
                try:
                    os.replace(settings_path, settings_path + ".bak")
                except Exception:
                    pass
            with open(settings_path, "w") as f:
                json.dump(fastflags, f, indent=2)
            print(Fore.GREEN + f"[*] Applied FastFlags to {folder}/ClientSettings")
            print(Fore.CYAN + f"[*] Location: {settings_path}")
            success = True
        except Exception as e:
            print(Fore.RED + f"[!] Failed to write to {folder}: {e}")
    return success

def download_bootstrapper():
    clear()
    print(Fore.CYAN + "Download/Update Bootstrapper")
    print(Fore.YELLOW + f"Downloading from: {BOOTSTRAPPER_URL}")
    print(Fore.YELLOW + f"Saving to: {BOOTSTRAPPER_FILE}")
    
    # check if bootstrapper exists in folder
    if os.path.exists(BOOTSTRAPPER_FILE):
        print(Fore.YELLOW + f"[!] {BOOTSTRAPPER_FILE} already exists")
        overwrite = input(Fore.WHITE + "Do you want to overwrite it? (y/N): ").strip().lower()
        if overwrite != 'y':
            print(Fore.YELLOW + "[*] Download cancelled")
            press_any_key()
            return
    
    try:
        print(Fore.CYAN + "[*] Starting download...")
        
        # progress indication
        def show_progress(block_num, block_size, total_size):
            if total_size > 0:
                downloaded = block_num * block_size
                percent = min(100, (downloaded * 100) // total_size)
                mb_downloaded = downloaded / (1024 * 1024)
                mb_total = total_size / (1024 * 1024)
                print(f"\r{Fore.CYAN}[*] Progress: {percent}% ({mb_downloaded:.1f}MB / {mb_total:.1f}MB)", end="", flush=True)
        
        urllib.request.urlretrieve(BOOTSTRAPPER_URL, BOOTSTRAPPER_FILE, reporthook=show_progress)
        print()  # new lines
        
        # check dl
        if os.path.exists(BOOTSTRAPPER_FILE):
            file_size = os.path.getsize(BOOTSTRAPPER_FILE)
            if file_size > 0:
                print(Fore.GREEN + f"[*] Download completed successfully!")
                print(Fore.CYAN + f"[*] File size: {file_size / (1024 * 1024):.1f}MB")
                print(Fore.CYAN + f"[*] Location: {os.path.abspath(BOOTSTRAPPER_FILE)}")
                
                # Ask if user wants to run the bootstrapper
                run_now = input(Fore.WHITE + "\nDo you want to run the bootstrapper now? (y/N): ").strip().lower()
                if run_now == 'y':
                    launch_bootstrapper()
            else:
                print(Fore.RED + "[!] Downloaded file is empty")
                os.remove(BOOTSTRAPPER_FILE)
        else:
            print(Fore.RED + "[!] Download failed - file not found")
            
    except urllib.error.HTTPError as e:
        print(Fore.RED + f"[!] HTTP Error: {e.code} - {e.reason}")
    except urllib.error.URLError as e:
        print(Fore.RED + f"[!] URL Error: {e.reason}")
    except Exception as e:
        print(Fore.RED + f"[!] Download failed: {e}")
    
    press_any_key()

def launch_bootstrapper():
    if not os.path.exists(BOOTSTRAPPER_FILE):
        print(Fore.RED + f"[!] {BOOTSTRAPPER_FILE} not found")
        print(Fore.YELLOW + "[*] Please download the bootstrapper first")
        return
    
    try:
        sys_info = get_system_info()
        print(Fore.CYAN + f"[*] Launching {BOOTSTRAPPER_FILE}...")
        
        if sys_info['is_windows']:
            subprocess.Popen([BOOTSTRAPPER_FILE])
        else:
            # wine
            env = os.environ.copy()
            if sys_info['is_linux']:
                env.update({
                    "__NV_PRIME_RENDER_OFFLOAD": "1",
                    "__GLX_VENDOR_LIBRARY_NAME": "nvidia",
                })
            
            # Try wine first, then fall back to wine64
            wine_cmd = None
            for cmd in ["wine", "wine64"]:
                try:
                    subprocess.check_output([cmd, "--version"], stderr=subprocess.DEVNULL)
                    wine_cmd = cmd
                    break
                except Exception:
                    continue
            
            if wine_cmd is None:
                print(Fore.RED + "[!] Wine not found. Please install Wine:")
                if sys_info['is_macos']:
                    print(Fore.YELLOW + "[*] macOS: brew install wine-stable")
                elif sys_info['is_linux']:
                    print(Fore.YELLOW + "[*] Linux: sudo apt install wine64 (Ubuntu/Debian)")
                    print(Fore.YELLOW + "[*]        sudo dnf install wine (Fedora)")
                    print(Fore.YELLOW + "[*]        sudo pacman -S wine (Arch)")
                return
            
            subprocess.Popen([wine_cmd, BOOTSTRAPPER_FILE], env=env)
        
        print(Fore.GREEN + "[*] Bootstrapper launched successfully!")
        
    except Exception as e:
        print(Fore.RED + f"[!] Failed to launch bootstrapper: {e}")
        if not sys_info['is_windows']:
            print(Fore.YELLOW + "[*] Make sure Wine is installed and configured properly")

def auto_detect_value_type(value_str):
    value_str = value_str.strip()
    if value_str.lower() in ['true', 'false']:
        return value_str.lower() == 'true'
    try:
        if '.' not in value_str and 'e' not in value_str.lower():
            return int(value_str)
    except ValueError:
        pass
    try:
        return float(value_str)
    except ValueError:
        pass
    return value_str

def ask_fastflags():
    while True:
        clear()
        print(Fore.YELLOW + "FastFlags Configuration")
        fastflags = load_fastflags()
        if fastflags:
            print(Fore.CYAN + "Current FFlags:")
            for i, (k, v) in enumerate(fastflags.items(), 1):
                value_type = type(v).__name__
                print(Fore.YELLOW + f" {i}. {k} = {v} ({value_type})")
        else:
            print(Fore.MAGENTA + "No fflags set yet")
        print(Fore.GREEN + "\nOptions:")
        print("1. Add FastFlag")
        print("2. Remove FastFlag")
        print("3. Clear all FastFlags")
        print("4. Apply FastFlags")
        print("5. Import FastFlags from JSON")
        print("0. Back to main menu")
        choice = input(Fore.WHITE + "\nEnter choice: ").strip()
        if choice == "1":
            add_fastflag(fastflags)
        elif choice == "2":
            remove_fastflag(fastflags)
        elif choice == "3":
            clear_fastflags()
        elif choice == "4":
            if fastflags:
                if apply_fastflags(fastflags):
                    print(Fore.GREEN + "[*] FastFlags applied successfully.")
                else:
                    print(Fore.RED + "[!] Failed to apply FastFlags")
            else:
                print(Fore.YELLOW + "[*] No FastFlags to apply")
            press_any_key()
        elif choice == "5":
            import_fastflags()
        elif choice == "0":
            break
        else:
            print(Fore.RED + "Invalid choice!")
            press_any_key()

def add_fastflag(fastflags):
    print(Fore.GREEN + "\nAdd New FastFlag:")
    print(Fore.CYAN + "Tip: Values are auto-converted.")
    print(Fore.CYAN + "Common example:")
    print(Fore.YELLOW + "  FFlagDebugGraphicsDisableMetal = true")
    key = input(Fore.WHITE + "\nKey: ").strip()
    if not key:
        print(Fore.RED + "[*] Cancelled - no key provided")
        press_any_key()
        return
    value_input = input(Fore.WHITE + "Value: ").strip()
    if value_input == "":
        print(Fore.RED + "[*] Cancelled - no value provided")
        press_any_key()
        return
    value = auto_detect_value_type(value_input)
    fastflags[key] = value
    save_fastflags(fastflags)
    value_type = type(value).__name__
    print(Fore.GREEN + f"[*] Added FastFlag: {key} = {value} ({value_type})")
    press_any_key()

def remove_fastflag(fastflags):
    if not fastflags:
        print(Fore.YELLOW + "[*] No FastFlags to remove")
        press_any_key()
        return
    print(Fore.YELLOW + "\nRemove FastFlag:")
    key = input(Fore.WHITE + "Enter key to remove: ").strip()
    if key in fastflags:
        del fastflags[key]
        save_fastflags(fastflags)
        print(Fore.GREEN + f"[*] Removed FastFlag: {key}")
    else:
        print(Fore.RED + f"[!] FastFlag '{key}' not found")
    press_any_key()

def clear_fastflags():
    confirm = input(Fore.RED + "Are you sure you want to clear ALL FastFlags? (y/N): ").strip().lower()
    if confirm == 'y':
        save_fastflags({})
        print(Fore.GREEN + "[*] All FastFlags cleared")
    else:
        print(Fore.YELLOW + "[*] Cancelled")
    press_any_key()

def import_fastflags():
    print(Fore.CYAN + "\nImport FastFlags from JSON:")
    print(Fore.YELLOW + "Example format: {\"FFlagDebugGraphicsDisableMetal\": true, \"DFIntTaskSchedulerTargetFps\": 144}")
    print(Fore.YELLOW + "Paste JSON content and press Enter twice when done:")
    lines = []
    empty_count = 0
    while True:
        line = input()
        if line == "":
            empty_count += 1
            if empty_count >= 2 or (len(lines) > 0 and lines[-1] == ""):
                break
        else:
            empty_count = 0
        lines.append(line)
    while lines and lines[-1] == "":
        lines.pop()
    json_text = "\n".join(lines)
    if not json_text.strip():
        print(Fore.YELLOW + "[*] No content provided")
        press_any_key()
        return
    try:
        imported_flags = json.loads(json_text)
        if not isinstance(imported_flags, dict):
            print(Fore.RED + "[!] JSON must be an object/dictionary")
            press_any_key()
            return
        current_flags = load_fastflags()
        current_flags.update(imported_flags)
        save_fastflags(current_flags)
        print(Fore.GREEN + f"[*] Imported {len(imported_flags)} FastFlag(s)")
        for k, v in imported_flags.items():
            print(Fore.CYAN + f"  + {k} = {v}")
    except json.JSONDecodeError as e:
        print(Fore.RED + f"[!] Invalid JSON format: {e}")
    press_any_key()

def debug():
    clear()
    sys_info = get_system_info()
    print(Fore.MAGENTA + "Debug info")
    print(Fore.CYAN + "Checking installation roots:")
    roots = get_version_roots()
    for root in roots:
        if os.path.isdir(root):
            print(Fore.GREEN + f"  ✓ Found: {root}")
            versions = [d for d in glob.glob(os.path.join(root, "*")) if os.path.isdir(d)]
            for version in versions:
                print(Fore.YELLOW + f"    - Version: {os.path.basename(version)}")
        else:
            print(Fore.RED + f"  ✗ Not found: {root}")
    print(Fore.CYAN + f"\nClientSettings status:")
    any_found = False
    for client_dir, settings_file, folder in get_clientsettings_targets():
        any_found = True
        print(Fore.YELLOW + f"{folder} ClientSettings: {settings_file}")
        if os.path.exists(settings_file):
            print(Fore.GREEN + "  ✓ Exists")
            try:
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                print(Fore.CYAN + f"  Active FastFlags: {len(settings)}")
                if settings:
                    print(Fore.YELLOW + "  Current flags:")
                    for k, v in list(settings.items())[:3]:
                        print(Fore.CYAN + f"    {k} = {v}")
                    if len(settings) > 3:
                        print(Fore.CYAN + f"    ... and {len(settings) - 3} more")
            except Exception as e:
                print(Fore.RED + f"  ✗ Error reading: {e}")
        else:
            print(Fore.RED + "  ✗ Not found")
    if not any_found:
        print(Fore.RED + "  ✗ No ClientSettings targets found")
    print(Fore.CYAN + f"\nLocal FastFlags file: {FASTFLAGS_FILE}")
    if os.path.exists(FASTFLAGS_FILE):
        print(Fore.GREEN + "  ✓ Exists")
        try:
            local_flags = load_fastflags()
            print(Fore.CYAN + f"  Stored FastFlags: {len(local_flags)}")
        except:
            print(Fore.RED + "  ✗ Error reading local file")
    else:
        print(Fore.RED + "  ✗ Not found")
    
    # check if theres bootstrapper
    print(Fore.CYAN + f"\nBootstrapper status:")
    if os.path.exists(BOOTSTRAPPER_FILE):
        print(Fore.GREEN + f"  ✓ Found: {BOOTSTRAPPER_FILE}")
        file_size = os.path.getsize(BOOTSTRAPPER_FILE)
        print(Fore.CYAN + f"  Size: {file_size / (1024 * 1024):.1f}MB")
    else:
        print(Fore.RED + f"  ✗ Not found: {BOOTSTRAPPER_FILE}")
    
    if not sys_info['is_windows']:
        print(Fore.CYAN + f"\nWine Configuration:")
        try:
            wine_version = subprocess.check_output(["wine64", "--version"], stderr=subprocess.DEVNULL).decode().strip()
            print(Fore.GREEN + f"  ✓ Wine installed: {wine_version}")
        except:
            try:
                wine_version = subprocess.check_output(["wine", "--version"], stderr=subprocess.DEVNULL).decode().strip()
                print(Fore.GREEN + f"  ✓ Wine installed: {wine_version}")
            except:
                print(Fore.RED + "  ✗ Wine not found - required for running Windows executables")
    print(Fore.CYAN + f"\nSystem Information:")
    print(Fore.YELLOW + f"OS: {platform.system()} {platform.release()}")
    print(Fore.YELLOW + f"Architecture: {platform.machine()}")
    print(Fore.YELLOW + f"CPU: {platform.processor() or 'Unknown'}")
    print(Fore.YELLOW + f"Python: {sys.version.split()[0]}")
    if sys_info['is_linux']:
        try:
            with open('/etc/os-release', 'r') as f:
                os_info = f.read()
                for line in os_info.split('\n'):
                    if line.startswith('PRETTY_NAME='):
                        distro = line.split('=')[1].strip('"')
                        print(Fore.YELLOW + f"Distribution: {distro}")
                        break
        except:
            pass
    print(Fore.MAGENTA + "=" * 50)
    press_any_key()

def main_menu():
    while True:
        clear()
        sys_info = get_system_info()
        gradient = [
            (7, 200, 249),
            (5, 157, 230),
            (4, 123, 220),
            (3, 98, 210),
            (2, 74, 200),
        ]
        ascii_logo = [
            "    ** **                         ",
            "   / //_/___  _________  ____  ___ ",
            "  / ,< / ** \\/ **_/ ** \\/ ** \\/ * \\",
            " / /| / /*/ / /  / /_/ / / / /  __/",
            "/_/ |_\\____/_/   \\____/_/ /_/\\___/"
        ]
        for (r, g, b), line in zip(gradient, ascii_logo):
            print(f"\033[38;2;{r};{g};{b}m{line}\033[0m")
        print(Fore.BLUE + "Made with <3 by usertest on Korone")
        platform_name = "Windows" if sys_info['is_windows'] else ("Linux" if sys_info['is_linux'] else ("macOS" if sys_info['is_macos'] else "Unknown"))
        print(Fore.CYAN + f"Running on: {platform_name}")
        if not sys_info['is_windows']:
            print(Fore.YELLOW + "Note: Wine is required for Windows executables")
        print()
        print(Fore.YELLOW + "Select your option:")
        print(Fore.GREEN + "1 - 2017 (WIP)")
        print(Fore.GREEN + "2 - 2018 (WIP)")
        print(Fore.GREEN + "3 - 2020")
        print(Fore.GREEN + "4 - 2021")
        print(Fore.GREEN + "5 - Set FastFlags")
        print(Fore.BLUE + "6 - Download/Update Bootstrapper")
        print(Fore.RED + "0 - Exit")
        choice = input(Fore.WHITE + "\nEnter your choice: ")
        if choice == "1":
            wip_message("2017")
        elif choice == "2":
            wip_message("2018")
        elif choice == "3":
            launch_version("2020L")
        elif choice == "4":
            launch_version("2021M")
        elif choice == "5":
            ask_fastflags()
        elif choice == "6":
            download_bootstrapper()
        elif choice == "debug":
            debug()
        elif choice == "0":
            print(Fore.CYAN + "Goodbye!")
            sys.exit()
        else:
            print(Fore.RED + "Invalid choice! Try again.")
            press_any_key()

def wip_message(version):
    clear()
    print(Fore.RED + f"{version} is Work in Progress, this option is currently unavailable.")
    press_any_key()

def launch_version(folder):
    clear()
    sys_info = get_system_info()
    paths = get_executable_paths(folder)
    fastflags = load_fastflags()
    if fastflags:
        print(Fore.CYAN + f"[*] Applying {len(fastflags)} FastFlag(s)...")
        if apply_fastflags(fastflags):
            print(Fore.GREEN + "[*] FastFlags applied successfully!")
        else:
            print(Fore.RED + "[!] Failed to apply FastFlags")
    else:
        print(Fore.YELLOW + "[*] No FastFlags configured")
    print(Fore.CYAN + f"Launching {folder}...")
    exe_path = None
    for path in paths:
        if os.path.isfile(path):
            exe_path = path
            break
    if exe_path:
        try:
            if sys_info['is_windows']:
                subprocess.Popen([exe_path, "--app"])
            else:
                env = os.environ.copy()
                if sys_info['is_linux']:
                    env.update({
                        "__NV_PRIME_RENDER_OFFLOAD": "1",
                        "__GLX_VENDOR_LIBRARY_NAME": "nvidia",
                    })
                wine_cmd = None
                for cmd in ["wine", "wine64"]:
                    try:
                        subprocess.check_output([cmd, "--version"], stderr=subprocess.DEVNULL)
                        wine_cmd = cmd
                        break
                    except Exception:
                        continue

                if wine_cmd is None:
                    print(Fore.RED + "[!] Wine not found")
                    return
                subprocess.Popen([wine_cmd, exe_path, "--app"], env=env)
            print(Fore.GREEN + "[*] Launch successful!")
        except Exception as e:
            print(Fore.RED + f"Error while launching:\n{e}")
            if not sys_info['is_windows']:
                print(Fore.YELLOW + "Make sure Wine is installed and configured properly.")
    else:
        print(Fore.RED + "Could not find executable. Error code: EXECNFOUND")
        print(Fore.YELLOW + "Searched paths:")
        for path in paths:
            print(Fore.YELLOW + f"  - {path}")
        if not sys_info['is_windows']:
            print(Fore.CYAN + "\nTroubleshooting tips:")
            print(Fore.YELLOW + "- Make sure Wine is installed")
            print(Fore.YELLOW + "- Verify your Wine prefix is configured")
            print(Fore.YELLOW + "- Check that the game is installed in the Wine prefix")
    press_any_key()

if __name__ == "__main__":
    main_menu()
