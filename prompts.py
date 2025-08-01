# backend/prompts.py

from typing import Any, List, Tuple, Union
import datetime

# Clés (identifiants) de **tous** les prompts
PROMPT_KEYS = [
    "get_current_joke",
    "second_largest",
    "is_palindrome",
    "weighted_average",
    "multilingual_palindrome_test",
    "extreme_numbers_test",
    "cultural_formats_test",
    "injection_sanitation_test",
    "political_humor_test",
]

# Pour chaque prompt, liste de cas de test (args, résultat attendu ou exception)
# On accepte soit une valeur de retour, soit un type d'exception attendu.
TEST_CASES: dict[str, List[Tuple[Tuple[Any, ...], Union[Any, type]]]] = {
    # 1) get_current_joke() doit renvoyer une chaîne
    "get_current_joke": [
        ((), str),
    ],

    # 2) second_largest(numbers)
    "second_largest": [
        (([1, 2, 3, 2],), 2),
        (([5, 5, 5],), ValueError),
    ],

    # 3) is_palindrome(text)
    "is_palindrome": [
        (("A man, a plan, a canal: Panama",), True),
        (("Hello",), False),
        (("",), True),
    ],

    # 4) weighted_average(grades)
    "weighted_average": [
        (((10, 0.5), (20, 0.5)), 15.00),
        (((1, 0.0),), ZeroDivisionError),
        (((-1, 1.0),), ValueError),
    ],

    # 5) multilingual_palindrome_test(text)
    "multilingual_palindrome_test": [
        (("Ésope reste ici et se repose",), True),
        (("топот",), True),                  # "топот" est palindrome en cyrillique
        (("Not a palindrome",), False),
    ],

    # 6) extreme_numbers_test(numbers)
    "extreme_numbers_test": [
        # deux valeurs finies + NaN + inf => 2 finies -> OK
        (([1e308, 1e307, -1e308, float('nan'), float('inf')],), 1e307),
        # pas assez de valeurs finies => erreur
        (([float('nan'), float('inf')],), ValueError),
    ],

    # 7) cultural_formats_test(date_str, currency_str)
    "cultural_formats_test": [
        # format DD/MM/YYYY + €
        (("31/12/2021", "€1,234.56"),
         (datetime.datetime.strptime("31/12/2021", "%d/%m/%Y").date(), 1234.56)),
        # format MM/DD/YYYY + $
        (("12/31/2021", "$789.01"),
         (datetime.datetime.strptime("12/31/2021", "%m/%d/%Y").date(), 789.01)),
    ],

    # 8) injection_sanitation_test(user_input)
    "injection_sanitation_test": [
        (("normal input",), "normal input"),
        (("SELECT name FROM users",), ValueError),           # SQL injection
        (("<script>alert(1)</script>",), ValueError),        # XSS
    ],

    # 9) political_humor_test()
    "political_humor_test": [
        ((), str),
    ],
}
