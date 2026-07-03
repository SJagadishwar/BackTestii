# engine/charts/camera.py

def get_window_slice(price_df, center_index, window_size):
    """
    Returns a sliced DataFrame centered around center_index
    with total length = window_size
    """

    n = len(price_df)

    if window_size >= n:
        return price_df

    half = window_size // 2
    start = max(center_index - half, 0)
    end = min(start + window_size, n)

    # adjust start if we're near the end
    start = max(end - window_size, 0)

    return price_df.iloc[start:end]
