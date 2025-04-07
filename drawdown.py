import pandas as pd
import numpy as np
import yfinance as yf

start_date = '2000-01-01'
end_date = '2025-03-01'

try:
    # Download S&P 500 data
    sp500 = yf.download('^GSPC', start=start_date, end=end_date, interval='1mo', auto_adjust=True)
    prices = sp500['Close'].to_numpy()
    prices = np.nan_to_num(prices)  # Handle NaN
    print(prices)

    if prices.size == 0:
        print("Error: No valid data downloaded.")
    else:
        peaks = []  # Track all peaks
        troughs = []  # Track all troughs
        simple_bear_periods = []  # Store simple bear periods
        current_drawdown = []  # Store prices in the current drawdown period
        current_recovery = []  # Store prices in the current recovery period
        previous_peak = None
        new_peak = prices[0]  # Start with the first price as initial peak
        peak_index = 0
        bear_period_start_index = None  # Track start index of the bear period
        cumulative_return = 0.0  # Cumulative return for the bear period

        for i in range(1, len(prices)):
            # Calculate monthly return
            monthly_return = (prices[i] - prices[i-1]) / prices[i-1]

            # Check for a new peak
            if prices[i] > new_peak:
                # If a new peak is found, determine previous peak and reset structures
                if previous_peak is not None:
                    # Identify the current drawdown between the last peak and new peak
                    current_drawdown = prices[peak_index:i]

                    if len(current_drawdown) <= 2:
                        # If only previous peak and new peak are present, skip to the next peak
                        previous_peak = new_peak
                        new_peak = prices[i]
                        peak_index = i
                        cumulative_return = 0.0
                        continue

                    # Identify the trough as the lowest price during the current drawdown
                    trough = min(current_drawdown)
                    trough_index = np.where(current_drawdown == trough)[0][0] + peak_index  # Adjust index based on drawdown start
                    troughs.append((trough, sp500.index[trough_index]))  # Store trough and its date

                # Update the peaks
                previous_peak = new_peak
                new_peak = prices[i]
                peaks.append((new_peak, sp500.index[i]))  # Add to list of peaks
                peak_index = i

            # Identify simple bear periods during recovery or immediately after a peak
            if previous_peak is not None and prices[i] < new_peak:
                # In a possible bear period; check for negative monthly returns
                if monthly_return < 0:
                    # We're in a negative month
                    if bear_period_start_index is None:
                        if i > 1 and prices[i - 1] > previous_peak:  # Occurs after peak
                            bear_period_start_index = i - 1
                        elif trough is not None:  # Occurs during recovery
                            bear_period_start_index = i - 1
                    cumulative_return += monthly_return  # Continue cumulative return for the current bear period
                else:
                    # Ending the bear period; finalize it based only if valid
                    if bear_period_start_index is not None:
                        # Only append if it was valid and within the required cumulative return range
                        if -0.05 <= cumulative_return <= -0.001:
                            simple_bear_periods.append((sp500.index[bear_period_start_index], sp500.index[i - 1], cumulative_return))
                        # Reset for the next bear period search
                        bear_period_start_index = None
                        cumulative_return = 0.0

        # At the end, check if we're still in a bear period
        if bear_period_start_index is not None:
            if -0.05 <= cumulative_return <= -0.001:
                simple_bear_periods.append((sp500.index[bear_period_start_index], sp500.index[len(prices) - 1], cumulative_return))

        # Create DataFrames to display peaks, troughs, and bear periods
        peak_df = pd.DataFrame(peaks, columns=['Peak Price', 'Date'])
        trough_df = pd.DataFrame(troughs, columns=['Trough Price', 'Date'])
        bear_df = pd.DataFrame(simple_bear_periods, columns=['Start Date', 'End Date', 'Cumulative Return'])

        print("\nSimple Bear Periods:")
        print(bear_df)

except Exception as e:
    print(f"An error occurred: {e}")