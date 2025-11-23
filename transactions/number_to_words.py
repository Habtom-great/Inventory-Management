from django import template
import math

register = template.Library()

NUM_NAMES = {
    0: 'Zero', 1: 'One', 2: 'Two', 3:'Three', 4:'Four', 5:'Five', 6:'Six', 7:'Seven', 8:'Eight', 9:'Nine', 10:'Ten',
    11:'Eleven',12:'Twelve',13:'Thirteen',14:'Fourteen',15:'Fifteen',16:'Sixteen',17:'Seventeen',18:'Eighteen',19:'Nineteen'
}
TENS_NAMES = {
    2:'Twenty',3:'Thirty',4:'Forty',5:'Fifty',6:'Sixty',7:'Seventy',8:'Eighty',9:'Ninety'
}

def convert_hundred(n):
    if n < 20:
        return NUM_NAMES[n]
    elif n < 100:
        div, mod = divmod(n, 10)
        return TENS_NAMES[div] + ('' if mod==0 else ' ' + NUM_NAMES[mod])
    else:
        div, mod = divmod(n,100)
        return NUM_NAMES[div] + ' Hundred' + ('' if mod==0 else ' ' + convert_hundred(mod))

def number_to_words(n):
    if n==0:
        return 'Zero'
    words = ''
    if n>=1000:
        div, mod = divmod(n,1000)
        words += convert_hundred(div) + ' Thousand '
        n = mod
    if n>0:
        words += convert_hundred(n)
    return words.strip()

@register.filter
def num2words(value):
    try:
        value = float(value)
        whole = int(math.floor(value))
        fraction = int(round((value-whole)*100))
        if fraction > 0:
            return f"{number_to_words(whole)} Birr and {number_to_words(fraction)} Cents"
        else:
            return f"{number_to_words(whole)} Birr"
    except:
        return ''
