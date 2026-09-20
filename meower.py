import ctypes
import os
import sys
if len(sys.argv) < 3:
    print(f"Usage: {sys.argv[0]} <appid> <achievement_api_name>")
    print(f"       {sys.argv[0]} <appid> --list")
    sys.exit(1)
app_id = sys.argv[1]
achievement_id = sys.argv[2].encode("utf-8")
os.environ["SteamAppId"] = app_id
os.environ["SteamGameId"] = app_id
open('steam_appid.txt','w').write(app_id)
dll_path = os.path.abspath("steam_api64.dll")
try:
    steam = ctypes.CDLL(dll_path, use_last_error=True)
except OSError as e:
    print(f"Failed to load steam_api64.dll: {e}")
    sys.exit(1)
steam.SteamAPI_InitSafe.argtypes = [ctypes.c_void_p]
steam.SteamAPI_InitSafe.restype = ctypes.c_bool
steam.SteamAPI_Shutdown.restype = None
steam.SteamAPI_Shutdown.argtypes = []
steam.SteamAPI_SteamUserStats_v013.restype = ctypes.c_void_p
steam.SteamAPI_SteamUserStats_v013.argtypes = []
steam.SteamAPI_ISteamUserStats_SetAchievement.restype = ctypes.c_bool
steam.SteamAPI_ISteamUserStats_SetAchievement.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
steam.SteamAPI_ISteamUserStats_ClearAchievement.restype = ctypes.c_bool
steam.SteamAPI_ISteamUserStats_ClearAchievement.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
steam.SteamAPI_ISteamUserStats_StoreStats.restype = ctypes.c_bool
steam.SteamAPI_ISteamUserStats_StoreStats.argtypes = [ctypes.c_void_p]
steam.SteamAPI_ISteamUserStats_GetNumAchievements.restype = ctypes.c_uint32
steam.SteamAPI_ISteamUserStats_GetNumAchievements.argtypes = [ctypes.c_void_p]
steam.SteamAPI_ISteamUserStats_GetAchievementName.restype = ctypes.c_char_p
steam.SteamAPI_ISteamUserStats_GetAchievementName.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
steam.SteamAPI_ISteamUserStats_GetAchievement.restype = ctypes.c_bool
steam.SteamAPI_ISteamUserStats_GetAchievement.argtypes = [
    ctypes.c_void_p, ctypes.c_char_p, ctypes.POINTER(ctypes.c_bool)
]
steam.SteamAPI_ISteamUserStats_GetAchievementAchievedPercent.restype = ctypes.c_bool
steam.SteamAPI_ISteamUserStats_GetAchievementAchievedPercent.argtypes = [
    ctypes.c_void_p, ctypes.c_char_p, ctypes.POINTER(ctypes.c_float)
]
if not steam.SteamAPI_InitSafe(None):
    win_err = ctypes.get_last_error()
    print(f"GetLastError={win_err}")
    print(f"SteamAPI_InitSafe failed.")
    sys.exit(1)
stats = steam.SteamAPI_SteamUserStats_v013()
if sys.argv[2] == "--restore":
    if len(sys.argv) < 4:
        print(f"Usage: {sys.argv[0]} <appid> --restore <file>")
        sys.exit(1)
    restore_file = sys.argv[3]
    try:
        with open(restore_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except OSError as e:
        print(f"Failed to read {restore_file}: {e}")
        steam.SteamAPI_Shutdown()
        sys.exit(1)
    to_set = []
    to_clear = []
    for line in lines:
        line = line.strip()
        if not line or line.lower().startswith("found "):
            continue
        if not line.startswith("["):
            continue
        close1 = line.find("]")
        if close1 == -1:
            continue
        marker = line[:close1 + 1]
        rest = line[close1 + 1:].strip()
        if not rest.startswith("["):
            continue
        close2 = rest.find("]")
        if close2 == -1:
            continue
        index = rest[:close2 + 1]
        name = rest[close2 + 1:].strip()
        if not name:
            continue
        inner = marker[1:-1].strip().upper()
        if inner == "X":
            to_set.append(name)
        else:
            to_clear.append(name)
    if not to_set and not to_clear:
        print("No achievement names found in file.")
        steam.SteamAPI_Shutdown()
        sys.exit(1)
    ok = 0
    fail = 0
    print(f"Setting {len(to_set)} achievement(s)...")
    for name in to_set:
        if steam.SteamAPI_ISteamUserStats_SetAchievement(stats, name.encode("utf-8")):
            print(f"  [X] {name}")
            ok += 1
        else:
            print(f"  Failed to set {name}")
            fail += 1
    print(f"Clearing {len(to_clear)} achievement(s)...")
    for name in to_clear:
        if steam.SteamAPI_ISteamUserStats_ClearAchievement(stats, name.encode("utf-8")):
            print(f"  [ ] {name}")
            ok += 1
        else:
            print(f"  Failed to clear {name}")
            fail += 1
    if not steam.SteamAPI_ISteamUserStats_StoreStats(stats):
        print("Failed to store stats")
        steam.SteamAPI_Shutdown()
        sys.exit(1)
    print(f"Restored: {ok} applied ({len(to_set)} set, {len(to_clear)} cleared), {fail} failed.")
    steam.SteamAPI_Shutdown()
    sys.exit(0)
if sys.argv[2] == "--list":
    num_achievements = steam.SteamAPI_ISteamUserStats_GetNumAchievements(stats)
    print(f"Found {num_achievements} achievements.")
    for i in range(num_achievements):
        ach_name_bytes = steam.SteamAPI_ISteamUserStats_GetAchievementName(stats, i)
        if ach_name_bytes:
            ach_name = ach_name_bytes.decode('utf-8')
            achieved = ctypes.c_bool(False)
            steam.SteamAPI_ISteamUserStats_GetAchievement(
                stats, ach_name_bytes, ctypes.byref(achieved)
            )
            marker = "[X]" if achieved.value else "[ ]"
            print(f"{marker} [{i}] {ach_name}")
    sys.exit(0)
elif sys.argv[2] == "--all":
        num_achievements = steam.SteamAPI_ISteamUserStats_GetNumAchievements(stats)
        print(f"Found {num_achievements} achievements.")
        for i in range(num_achievements):
            ach_name_bytes = steam.SteamAPI_ISteamUserStats_GetAchievementName(stats, i)
            if ach_name_bytes:
                ach_name = ach_name_bytes.decode('utf-8')
                if len(sys.argv) > 3:
                    if sys.argv[3] == "false":
                        print(f"Clearing achievement {ach_name}")
                        steam.SteamAPI_ISteamUserStats_ClearAchievement(stats, ach_name_bytes)
                    elif sys.argv[3] == "true":
                        print(f"Setting achievement {ach_name}")
                        steam.SteamAPI_ISteamUserStats_SetAchievement(stats, ach_name_bytes)
                else:
                    print(f"Setting achievement {ach_name} to true because no argument was provided")
                    steam.SteamAPI_ISteamUserStats_SetAchievement(stats, ach_name_bytes)
        sys.exit(0)
if sys.argv[2] == "--rarest":
    num_achievements = steam.SteamAPI_ISteamUserStats_GetNumAchievements(stats)
    rarest_name = None
    rarest_percent = 100.0
    for i in range(num_achievements):
        ach_name_bytes = steam.SteamAPI_ISteamUserStats_GetAchievementName(stats, i)
        if not ach_name_bytes:
            continue
        ach_name = ach_name_bytes.decode('utf-8')
        percent = ctypes.c_float(0.0)
        if steam.SteamAPI_ISteamUserStats_GetAchievementAchievedPercent(
            stats, ach_name_bytes, ctypes.byref(percent)
        ):
            if percent.value < rarest_percent:
                rarest_percent = percent.value
                rarest_name = ach_name
    if rarest_name:
        print(f"Rarest achievement: {rarest_name} ({rarest_percent:.2f}% of players have it)")
    else:
        print("Could not retrieve achievement percentages.")
    sys.exit(0)
if not stats:
    print("Failed to get ISteamUserStats interface")
    steam.SteamAPI_Shutdown()
    sys.exit(1)
if len(sys.argv) > 3:
    if sys.argv[3] == "false":
        if not steam.SteamAPI_ISteamUserStats_ClearAchievement(stats, achievement_id):
            print("Failed to clear achievement")
            steam.SteamAPI_Shutdown()
            sys.exit(1)
if not steam.SteamAPI_ISteamUserStats_SetAchievement(stats, achievement_id):
    print("Failed to set achievement")
    steam.SteamAPI_Shutdown()
    sys.exit(1)
if not steam.SteamAPI_ISteamUserStats_StoreStats(stats):
    print("Failed to store stats")
    steam.SteamAPI_Shutdown()
    sys.exit(1)
print("Achievement set successfully")
steam.SteamAPI_Shutdown()
