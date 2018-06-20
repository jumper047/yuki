def text_to_number(self, text):
    """
    Function transform all numbers (0-999 for now) in sentence from text to digits
    """
    numbers = {
        "ноль": 0,
        "один": 1,
        "два": 2,
        "три": 3,
        "четыре": 4,
        "пять": 5,
        "шесть": 6,
        "семь": 7,
        "восемь": 8,
        "девять": 9,
        "десять": 10,
        "одинадцать": 11,
        "двенадцать": 12,
        "тринадцать": 13,
        "четырнадцать": 14,
        "пятнадцать": 15,
        "шестнадцать": 16,
        "семнадцать": 17,
        "восемнадцать": 18,
        "девятнадцать": 19,
        "двадцать": 20,
        "тридцать": 30,
        "сорок": 40,
        "пятьдесят": 50,
        "шестьдесят": 60,
        "семьдесят": 70,
        "восемьдесят": 80,
        "девяносто": 90,
        "сто": 100,
        "двести": 200,
        "триста": 300,
        "четыреста": 400,
        "пятьсот": 500,
        "шестьсот": 600,
        "семьсот": 700,
        "восемьсот": 800,
        "девятьсот": 900,
        "тысяча": 1000
    }
    words = text.split(' ')
    for n in range(0, len(words)):
        if words[n] in numbers:
            n1000 = 0
            n100 = 0
            n20 = 0
            n10 = 0
            n1 = 0
            if numbers[words[n]] < 20:
                words[n] = str(numbers[words[n]])
            elif 20 <= numbers[words[n]] < 100:
                n10 = numbers[words[n]]
                if len(words) >= n + 2 and words[n + 1] in numbers and numbers[words[n + 1]] < 10:
                    n1 = numbers[words[n + 1]]
                    del(words[n + 1])
                words[n] = str(n10 + n1)
            elif 100 <= numbers[words[n]] < 1000:
                n100 = numbers[words[n]]
                if len(words) >= n + 2 and words[n + 1] in numbers and 20 <= numbers[words[n + 1]] < 100:
                    n10 = numbers[words[n + 1]]
                    if len(words) >= n + 3 and words[n + 2] in numbers and 1 <= numbers[words[n + 2]] < 10:
                        n1 = numbers[words[n + 2]]
                        del(words[n + 2])
                    del(words[n + 1])
                elif len(words) >= n + 2 and words[n + 1] in numbers and 1 <= numbers[words[n + 1]] < 20:
                    n20 = numbers[words[n + 1]]
                    del(words[n + 1])
                words[n] = str(n100 + n20 + n10 + n1)
            # elif number [word] == 1000:
            #     pass
        if n == len(words) - 1:
            break
    return " ".join(words)
