from toqito.states import chessboard


def extremal_PPT_chessboard():
    return chessboard([3 / 5, -3 / 5, 6 / 5, -6 / 5, -3 / 5, -3 / 5])


if __name__ == "__main__":
    print(extremal_PPT_chessboard())
