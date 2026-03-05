def buyer_utility(price, max_price):
    return max_price - price


def seller_utility(price, min_price):
    return price - min_price
