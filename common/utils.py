from typing import Any

def get_log_ansi_code() -> str:
    return '\33[97m'

def get_tag_ansi_code() -> str:
    return '\33[36m'

def get_plex_ansi_code() -> str:
    return '\33[93m'

def get_emby_ansi_code() -> str:
    return '\33[92m'

def get_jellyfin_ansi_code() -> str:
    return '\33[95m'
    
def get_log_header(module_ansi_code: str, module: str) -> str:
    return '{}{}{}:'.format(module_ansi_code, module, get_log_ansi_code())
    
def get_tag(tag_name: str, tag_value: Any) -> str:
    return '{}{}={}{}'.format(get_tag_ansi_code(), tag_name, get_log_ansi_code(), tag_value)

def get_formatted_plex() -> str:
    return '{}Plex{}'.format(get_plex_ansi_code(), get_log_ansi_code())

def get_formatted_emby() -> str:
    return '{}Emby{}'.format(get_emby_ansi_code(), get_log_ansi_code())

def get_formatted_jellyfin() -> str:
    return '{}Jellyfin{}'.format(get_jellyfin_ansi_code(), get_log_ansi_code())

def remove_ansi_code_from_text(text: str) -> str:
    plain_text = text
    while True:
        index = plain_text.find('\33[')
        if (index < 0):
            break
        else:
            end_index = plain_text.find('m', index)
            if end_index < 0:
                break
            else:
                end_index += 1
                plain_text = plain_text[:index] + plain_text[end_index:]
    return plain_text

def build_target_string(current_target: str, new_target: str, library: str):
    if current_target != '':
        return current_target + ' & {}:{}'.format(new_target, library)
    else:
        return '{}:{}'.format(new_target, library)
