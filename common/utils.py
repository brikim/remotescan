from typing import Any

ansi_start_code: str = "\33[38;5;"
ansi_end_code: str = "m"

ansi_code_log = f"{ansi_start_code}15{ansi_end_code}"
ansi_code_tag = f"{ansi_start_code}37{ansi_end_code}"
ansi_code_plex = f"{ansi_start_code}220{ansi_end_code}"
ansi_code_emby = f"{ansi_start_code}77{ansi_end_code}"
ansi_code_jellyfin = f"{ansi_start_code}63{ansi_end_code}"

def get_log_ansi_code() -> str:
    return ansi_code_log

def get_tag_ansi_code() -> str:
    return ansi_code_tag

def get_plex_ansi_code() -> str:
    return ansi_code_plex

def get_emby_ansi_code() -> str:
    return ansi_code_emby

def get_jellyfin_ansi_code() -> str:
    return ansi_code_jellyfin
    
def get_log_header(module_ansi_code: str, module: str) -> str:
    return f"{module_ansi_code}{module}{get_log_ansi_code()}:"
    
def get_tag(tag_name: str, tag_value: Any) -> str:
    return f"{ansi_code_tag}{tag_name}={ansi_code_log}{tag_value}"

def get_formatted_plex() -> str:
    return f"{ansi_code_plex}Plex{ansi_code_log}"

def get_formatted_emby() -> str:
    return f"{ansi_code_emby}Emby{ansi_code_log}"

def get_formatted_jellyfin() -> str:
    return f"{ansi_code_jellyfin}Jellyfin{ansi_code_log}"

def remove_ansi_code_from_text(text: str) -> str:
    plain_text = text
    while True:
        index = plain_text.find(ansi_start_code)
        if (index < 0):
            break
        else:
            end_index = plain_text.find(ansi_end_code, index)
            if end_index < 0:
                break
            else:
                end_index += 1
                plain_text = plain_text[:index] + plain_text[end_index:]
    return plain_text

def build_target_string(current_target: str, new_target: str, library: str) -> str:
    if current_target != "":
        if library == "":
            return current_target + f" & {new_target}"
        else:
            return current_target + f" & {new_target}:{library}"
    else:
        if library == "":
            return new_target
        else:
            return f"{new_target}:{library}"
