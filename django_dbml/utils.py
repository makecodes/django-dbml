import re


snake_pattern = re.compile(r"(?<!^)(?=[A-Z])")


def to_snake_case(value):
    value = snake_pattern.sub("_", value).lower()
    value = value.replace("i_p_", "ip_").replace("u_r_l", "url").replace("u_u_i_d", "uuid").replace("j_s_o_n", "json")

    return value
