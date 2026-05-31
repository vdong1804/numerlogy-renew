"""Vietnamese letter → numerology value mapping + accent stripping.

Ported verbatim from numerology/apis/constans.py and views.py.
"""

# Maps ASCII lowercase letter → {value: int, is_vowel: bool}
alphabet: dict[str, dict] = {
    'a': {'value': 1, 'is_vowel': True},
    'b': {'value': 2, 'is_vowel': False},
    'c': {'value': 3, 'is_vowel': False},
    'd': {'value': 4, 'is_vowel': False},
    'e': {'value': 5, 'is_vowel': True},
    'f': {'value': 6, 'is_vowel': False},
    'g': {'value': 7, 'is_vowel': False},
    'h': {'value': 8, 'is_vowel': False},
    'i': {'value': 9, 'is_vowel': True},
    'j': {'value': 1, 'is_vowel': False},
    'k': {'value': 2, 'is_vowel': False},
    'l': {'value': 3, 'is_vowel': False},
    'm': {'value': 4, 'is_vowel': False},
    'n': {'value': 5, 'is_vowel': False},
    'o': {'value': 6, 'is_vowel': True},
    'p': {'value': 7, 'is_vowel': False},
    'q': {'value': 8, 'is_vowel': False},
    'r': {'value': 9, 'is_vowel': False},
    's': {'value': 1, 'is_vowel': False},
    't': {'value': 2, 'is_vowel': False},
    'u': {'value': 3, 'is_vowel': True},
    'v': {'value': 4, 'is_vowel': False},
    'w': {'value': 5, 'is_vowel': False},
    'x': {'value': 6, 'is_vowel': False},
    'y': {'value': 7, 'is_vowel': False},
    'z': {'value': 8, 'is_vowel': False},
}

# Vietnamese accented → ASCII mapping
_S1 = 'ÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝàáâãèéêìíòóôõùúýĂăĐđĨĩŨũƠơƯưẠạẢảẤấẦầẨẩẪẫẬậẮắẰằẲẳẴẵẶặẸẹẺẻẼẽẾếỀềỂểỄễỆệỈỉỊịỌọỎỏỐốỒồỔổỖỗỘộỚớỜờỞởỠỡỢợỤụỦủỨứỪừỬửỮữỰựỲỳỴỵỶỷỸỹ'
_S0 = 'AAAAEEEIIOOOOUUYaaaaeeeiioooouuyAaDdIiUuOoUuAaAaAaAaAaAaAaAaAaAaAaAaEeEeEeEeEeEeEeEeIiIiOoOoOoOoOoOoOoOoOoOoOoOoUuUuUuUuUuUuUuYyYyYyYy'


def strip_accents(input_str: str) -> str:
    """Remove Vietnamese diacritical marks → plain ASCII.

    Ported verbatim from views.py:strip_accents().
    """
    result = ''
    for c in input_str:
        if c in _S1:
            result += _S0[_S1.index(c)]
        else:
            result += c
    return result
