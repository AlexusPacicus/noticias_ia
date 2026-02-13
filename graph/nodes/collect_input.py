def collect_input(state: dict) -> dict:
    if state is None:
        raise ValueError("EMPTY_INPUT_PAYLOAD")
    return {"input_raw": state.copy()}
