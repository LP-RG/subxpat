
def get_constant_bits_for_interval(interval: tuple[int, int], num_bits: int | None = None) -> dict[int, bool]:
    """
        Computes which bits never change in the given interval.

        :param interval: lower and upper bounds of the interval.
        :param num_bits: how many bits in total the number is composed of.
        :return: the assignments `True`/`False` for the bits that never change.
    """

    # args and guards
    min_val, max_val = interval
    if num_bits is None:
        num_bits = max(min_val.bit_length(), max_val.bit_length())
    elif min_val.bit_length() > num_bits or max_val.bit_length() > num_bits:
        raise RuntimeError('interval bounds are larger than num_bits')

    # iterate over bits from most to least significant, recording the bit value, stopping on first diff
    constant_bits = dict[int, bool]()
    for i in range(num_bits - 1, -1, -1):
        _mask = 1 << i
        _min_bit = min_val  & _mask
        _max_bit = max_val  & _mask
        if _min_bit != _max_bit: break
        constant_bits[i] = bool(_min_bit)

    return constant_bits
