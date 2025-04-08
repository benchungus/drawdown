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
        bearPeriods = []  # Store simple bear periods
        drawdownPeriods = []  # Store prices in the current drawdown period
        recoveryPeriods = []  # Store prices in the current recovery period
        currBears = []
        
        startingBear = None
        cumulativeBear = 0
        currMax = 0
        maxIdx = -1 
        troughIdx, currTrough = -1, -1

        for i in range(1, len(prices)):
            left, right = prices[i - 1], prices[i]
            leftIdx, rightIdx = i - 1, i
            change = (right - left) / left
            if change < 0:
                if left > currMax:
                    if peaks:
                        troughs.append((currTrough, sp500.index[troughIdx]))
                        drawdownPeriods.append((sp500.index[maxIdx], sp500.index[troughIdx], (currTrough - currMax) / currMax ))
                        recoveryPeriods.append((sp500.index[troughIdx], sp500.index[leftIdx], (left - currTrough) / currTrough ))
                        bearPeriods.extend(currBears)
                        currBears = []
                    currTrough, troughIdx = right, rightIdx
                    peaks.append((left, sp500.index[leftIdx]))
                    currMax, maxIdx = left, leftIdx
                if right < currTrough:
                    currBears = []
                    currTrough, troughIdx = right, rightIdx
                if cumulativeBear < 0:
                    if cumulativeBear + change < -.05:
                        currBears.append((sp500.index[startingBear], sp500.index[leftIdx], cumulativeBear))
                        cumulativeBear = 1
                elif cumulativeBear == 0:
                    if change < -.05:
                        cumulativeBear = 1
                    else:
                        startingBear = leftIdx
                        cumulativeBear += change
            else:
                if cumulativeBear < 0:
                    currBears.append((sp500.index[startingBear], sp500.index[leftIdx], cumulativeBear))
                cumulativeBear = 0

        # Create DataFrames to display peaks, troughs, and bear periods
        peak_df = pd.DataFrame(peaks, columns=['Peak Price', 'Date'])
        trough_df = pd.DataFrame(troughs, columns=['Trough Price', 'Date'])
        drawdown_df = pd.DataFrame(drawdownPeriods, columns=['Start Date', 'End Date', 'Cumulative Return'])
        recovery_df = pd.DataFrame(recoveryPeriods, columns=['Start Date', 'End Date', 'Cumulative Return'])
        bear_df = pd.DataFrame(bearPeriods, columns=['Start Date', 'End Date', 'Cumulative Return'])

        print("\nPeaks:")
        print(peak_df)
        print("\nTroughs:")
        print(trough_df)
        print("\nDrawdown Periods:")
        print(drawdown_df)
        print("\nRecovery Periods:")
        print(recovery_df)
        print("\nSimple Bear Periods:")
        print(bear_df)

except Exception as e:
    print(f"An error occurred: {e}")