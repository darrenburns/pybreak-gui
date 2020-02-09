from pybreak_gui.app import set_trace


def main():
    set_trace()
    x = 1
    y = 2
    z = x + y + 3
    print(z)


if __name__ == '__main__':
    main()
