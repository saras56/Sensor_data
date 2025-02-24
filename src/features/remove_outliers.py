import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math
import scipy
from sklearn.neighbors import LocalOutlierFactor  # pip install scikit-learn
%matplotlib inline
# --------------------------------------------------------------
# Load data
# --------------------------------------------------------------

df = pd.read_pickle("../../data/interim/01_data_processed.pkl")

outlier_columns= list(df.columns[:6])
# --------------------------------------------------------------
# Plotting outliers
# --------------------------------------------------------------
# in this case oulier could mean, data that cmes from 
# adjusting positions while doing exercises. this sort 
# of data has to remmoved otherwise it could be mistaken 
# for different exercise positions which will result 
# in poor model performance

plt.style.use("ggplot")
plt.rcParams["figure.figsize"] = (20, 5)
plt.rcParams["figure.dpi"] = 100


df[["acc_x", "label"]].boxplot(by="label", figsize=(20, 10))
plt.show()
df[outlier_columns[:3] + ["label"]].boxplot(by="label", figsize=(20, 10), layout=(1,3))
df[outlier_columns[3:] + ["label"]].boxplot(by="label", figsize=(20, 10), layout=(1,3))

def plot_binary_outliers(dataset, col, outlier_col, reset_index):
    """ Plot outliers in case of a binary outlier score. Here, the col specifies the real data
    column and outlier_col the columns with a binary value (outlier or not).

    Args:
        dataset (pd.DataFrame): The dataset
        col (string): Column that you want to plot
        outlier_col (string): Outlier column marked with true/false
        reset_index (bool): whether to reset the index for plotting
    """

    # Taken from: https://github.com/mhoogen/ML4QS/blob/master/Python3Code/util/VisualizeDataset.py

    dataset = dataset.dropna(axis=0, subset=[col, outlier_col])
    dataset[outlier_col] = dataset[outlier_col].astype("bool")

    if reset_index:
        dataset = dataset.reset_index()

    fig, ax = plt.subplots()

    plt.xlabel("samples")
    plt.ylabel("value")

    # Plot non outliers in default color
    ax.plot(
        dataset.index[~dataset[outlier_col]],
        dataset[col][~dataset[outlier_col]],
        "b+",
    )
    # Plot data points that are outliers in red
    ax.plot(
        dataset.index[dataset[outlier_col]],
        dataset[col][dataset[outlier_col]],
        "r+",
    )

    plt.legend(
        ["no outlier " + col,"outlier " + col],
        loc="upper center",
        ncol=2,
        fancybox=True,
        shadow=True,
    )
    plt.show()

# --------------------------------------------------------------
# Interquartile range (distribution based)
# --------------------------------------------------------------

# Insert IQR function

def mark_outliers_iqr(dataset, col):
    """Function to mark values as outliers using the IQR method.

    Args:
        dataset (pd.DataFrame): The dataset
        col (string): The column you want apply outlier detection to

    Returns:
        pd.DataFrame: The original dataframe with an extra boolean column 
        indicating whether the value is an outlier or not.
    """

    dataset = dataset.copy()

    Q1 = dataset[col].quantile(0.25)
    Q3 = dataset[col].quantile(0.75)
    IQR = Q3 - Q1

    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR

    dataset[col + "_outlier"] = (dataset[col] < lower_bound) | (
        dataset[col] > upper_bound
    )

    return dataset  

# Plot a single column
col = "acc_x"
dataset = mark_outliers_iqr(df, col)
plot_binary_outliers(dataset=dataset, col=col, outlier_col=col+"_outlier", reset_index=True)



# Loop over all columns
for col in outlier_columns:
    dataset = mark_outliers_iqr(df, col)
    plot_binary_outliers(dataset=dataset, col=col, outlier_col=col+"_outlier", reset_index=True)    
# Observation: this distribution based outlier detection method throws a 
# lot of data as outliers. Might lead to info loss   

# --------------------------------------------------------------
# Chauvenets criteron (distribution based)
# --------------------------------------------------------------
# outliers if the prob of occurence is less than 1/2N
# Check for normal distribution as Chauvenets criterion is applied on 
# normally distributed data 

df[outlier_columns[:3] + ["label"]].plot.hist(by="label", figsize=(20, 20), layout=(3,3))
df[outlier_columns[3:] + ["label"]].plot.hist(by="label", figsize=(20, 20), layout=(3,3))

# Insert Chauvenet's function

def mark_outliers_chauvenet(dataset, col, C=2):
    """Finds outliers in the specified column of datatable and adds a binary column with
    the same name extended with '_outlier' that expresses the result per data point.
    
    Taken from: https://github.com/mhoogen/ML4QS/blob/master/Python3Code/Chapter3/OutlierDetection.py

    Args:
        dataset (pd.DataFrame): The dataset
        col (string): The column you want apply outlier detection to
        C (int, optional): Degree of certainty for the identification of outliers given the assumption 
                           of a normal distribution, typicaly between 1 - 10. Defaults to 2.

    Returns:
        pd.DataFrame: The original dataframe with an extra boolean column 
        indicating whether the value is an outlier or not.
    """

    dataset = dataset.copy()
    # Compute the mean and standard deviation.
    mean = dataset[col].mean()
    std = dataset[col].std()
    N = len(dataset.index)
    criterion = 1.0 / (C * N)

    # Consider the deviation for the data points.
    deviation = abs(dataset[col] - mean) / std

    # Express the upper and lower bounds.
    low = -deviation / math.sqrt(C)
    high = deviation / math.sqrt(C)
    prob = []
    mask = []

    # Pass all rows in the dataset.
    for i in range(0, len(dataset.index)):
        # Determine the probability of observing the point
        prob.append(
            1.0 - 0.5 * (scipy.special.erf(high[i]) - scipy.special.erf(low[i]))
        )
        # And mark as an outlier when the probability is below our criterion.
        mask.append(prob[i] < criterion)
    dataset[col + "_outlier"] = mask
    return dataset


# Loop over all columns
for col in outlier_columns:
    dataset = mark_outliers_chauvenet(df, col)
    plot_binary_outliers(dataset=dataset, col=col, outlier_col=col+"_outlier", reset_index=True)    
# Observation: the no of outliers detected are reduced. This is a distribution based 
# outlier detection
# --------------------------------------------------------------
# Local outlier factor (distance based)
# --------------------------------------------------------------

# Insert LOF function

def mark_outliers_lof(dataset, columns, n=20):
    """Mark values as outliers using LOF

    Args:
        dataset (pd.DataFrame): The dataset
        col (string): The column you want apply outlier detection to
        n (int, optional): n_neighbors. Defaults to 20.
    
    Returns:
        pd.DataFrame: The original dataframe with an extra boolean column
        indicating whether the value is an outlier or not.
    """
    
    dataset = dataset.copy()

    lof = LocalOutlierFactor(n_neighbors=n)
    data = dataset[columns]
    outliers = lof.fit_predict(data)
    X_scores = lof.negative_outlier_factor_

    dataset["outlier_lof"] = outliers == -1
    return dataset, outliers, X_scores

# Loop over all columns
dataset, outliers, X_scores = mark_outliers_lof(df, outlier_columns) #we dont loop throu this fn.directly giving outlier col as i/p
for col in outlier_columns:
    plot_binary_outliers(dataset=dataset, col=col, outlier_col="outlier_lof", reset_index=True)    
# Observation: Lof outliers are based on distance and clustering of points. Here 
# the outliers within data is identified ie if outliers form a cluster , it is considered 
# as regular points

# --------------------------------------------------------------
# Check outliers grouped by label
# --------------------------------------------------------------

label = "squat"
for col in outlier_columns:
    dataset = mark_outliers_iqr(df[df['label']==label], col)
    plot_binary_outliers(dataset=dataset, col=col, outlier_col=col+"_outlier", reset_index=True)    


for col in outlier_columns:
    dataset = mark_outliers_chauvenet(df[df['label']==label], col)
    plot_binary_outliers(dataset=dataset, col=col, outlier_col=col+"_outlier", reset_index=True)    

dataset, outliers, X_scores = mark_outliers_lof(df[df['label']==label], outlier_columns) #we dont loop throu this fn.directly giving outlier col as i/p
for col in outlier_columns:
    plot_binary_outliers(dataset=dataset, col=col, outlier_col="outlier_lof", reset_index=True)    

# --------------------------------------------------------------
# Choose method and deal with outliers
# --------------------------------------------------------------

# Test on single column

col = "gyr_z"
dataset = mark_outliers_chauvenet(df, col)
dataset[dataset['gyr_z_outlier']]

dataset.loc[dataset['gyr_z_outlier'],"gyr_z"] =np.nan


# Create a loop

outliers_removed_df = df.copy()
for col in outlier_columns:
    for label in df['label'].unique():
        dataset = mark_outliers_chauvenet(df[df['label']==label], col)

        #Repalce values marked as outliers with Nan
        dataset.loc[dataset[col+"_outlier"],col] =np.nan
        
        #Update the column in the original dataframe
        outliers_removed_df.loc[(outliers_removed_df['label']==label),col] = dataset[col]
        
        n_outliers = len(dataset)-len(dataset[col].dropna())
        print(f"Removed {n_outliers} from {col} for {label}")
        
outliers_removed_df.info()       
        
        
# --------------------------------------------------------------
# Export new dataframe
# --------------------------------------------------------------
outliers_removed_df.to_pickle("../../data/interim/02_outliers_removed_chauvenets.pkl")