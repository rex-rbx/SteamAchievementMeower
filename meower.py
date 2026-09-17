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
if not steam.SteamAPI_InitSafe(None):
    win_err = ctypes.get_last_error()
    print(f"GetLastError={win_err}")
    print(f"SteamAPI_InitSafe failed.")
    sys.exit(1)
stats = steam.SteamAPI_SteamUserStats_v013()
if sys.argv[2] == "--list":
    num_achievements = steam.SteamAPI_ISteamUserStats_GetNumAchievements(stats)
    print(f"Found {num_achievements} achievements.")
    for i in range(num_achievements):
        ach_name_bytes = steam.SteamAPI_ISteamUserStats_GetAchievementName(stats, i)
        if ach_name_bytes:
            ach_name = ach_name_bytes.decode('utf-8')
            print(f"[{i}] {ach_name}")
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
