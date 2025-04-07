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
        trough = None

        for i in range(1, len(prices)):
            # Calculate monthly return
            monthly_return = (prices[i] - prices[i-1]) / prices[i-1]

            # Check for a new peak
            if prices[i] > new_peak:
                # When a new peak is found
                if previous_peak is not None:
                    # Add prices from previous peak to new peak to the current drawdown list
                    current_drawdown = prices[peak_index:i]

                    if len(current_drawdown) == 2:
                        # If the drawdown has only the previous peak and new peak, continue to next iteration
                        previous_peak = new_peak
                        new_peak = prices[i]
                        peak_index = i
                        continue

                    # Identify trough as the lowest price in the current drawdown
                    trough = min(current_drawdown)
                    trough_index = np.where(current_drawdown == trough)[0][0] + peak_index
                    troughs.append((trough, sp500.index[trough_index]))  # Store trough and its date

                # Update the peaks
                previous_peak = new_peak
                new_peak = prices[i]
                peaks.append((new_peak, sp500.index[i]))  # Add to the list of peaks
                peak_index = i  # Update the peak index for the next potential drawdown

            # Logic for bear period detection
            if previous_peak is not None and prices[i] < new_peak:
                # Check to see if we're in a bear period immediately after the previous peak
                if monthly_return < 0:
                    if bear_period_start_index is None:
                        # Check the first monthly return after the previous peak
                        if i == peak_index + 1 and (monthly_return >= -0.05 and monthly_return <= -0.001):
                            bear_period_start_index = i  # Start the bear period
                    cumulative_return += monthly_return  # Cumulative return for the current bear period
                else:
                    # Possible end of a bear period
                    if bear_period_start_index is not None:
                        # Check if the bear period is valid
                        if -0.05 <= cumulative_return <= -0.001:
                            simple_bear_periods.append((sp500.index[bear_period_start_index], sp500.index[i - 1],
                                                        cumulative_return))
                        # Reset for the next bear period search
                    bear_period_start_index = None
                    cumulative_return = 0.0

            # Logic for checking the recovery period after the trough
            if trough is not None and prices[i] >= new_peak:
                # We are in recovery; analyze the recovery period for potential bear periods
                if prices[i-1] > trough:
                    # Last price was a positive return after a trough
                    if monthly_return < 0 and (i > trough_index):
                        # Start the bear period if we have a negative return after the trough
                        if bear_period_start_index is None:
                            bear_period_start_index = i  # Start a new bear period
                else:
                    # If there's a positive return a bear period ends
                    if bear_period_start_index is not None:
                        if -0.05 <= cumulative_return <= -0.001:
                            simple_bear_periods.append((sp500.index[bear_period_start_index], sp500.index[i - 1],
                                                        cumulative_return))

            # Reset for the next analysis if a bear period is determined
            if bear_period_start_index is None:
                cumulative_return = 0.0  # Reset cumulative return

        # At the end, check if we're still in a bear period
        if bear_period_start_index is not None:
            if -0.05 <= cumulative_return <= -0.001:
                simple_bear_periods.append((sp500.index[bear_period_start_index], sp500.index[len(prices) - 1], cumulative_return))

        # Create DataFrames to display peaks, troughs, and bear periods
        peak_df = pd.DataFrame(peaks, columns=['Peak Price', 'Date'])
        trough_df = pd.DataFrame(troughs, columns=['Trough Price', 'Date'])
        bear_df = pd.DataFrame(simple_bear_periods, columns=['Start Date', 'End Date', 'Cumulative Return'])

        print("\nPeaks:")
        print(peak_df)
        print("\nTroughs:")
        print(trough_df)
        print("\nSimple Bear Periods:")
        print(bear_df)

except Exception as e:
    print(f"An error occurred: {e}")