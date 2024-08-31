### The data are from an experimental study that compared various treatments for young girls suffering from anorexia. For each girl, weight was measured before and after a fixed period of treatment. Courtesy/copyright of Prof. Brian Everitt, King’s College, London. ###

#Importing all the necessary libraries to upload the data, do statitics and plots

!pip install pingouin
import pingouin as pg #statistical package
import pandas as pd
import numpy as np
import scipy.stats as stats
from scipy.stats import ttest_ind, ttest_ind_from_stats
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
from statsmodels.stats.anova import AnovaRM

#Upload data
df_an = pd.read_csv("https://users.stat.ufl.edu/~aa/smss/data/Anorexia.dat", sep='\s+') #\s+ matches any whitespace (spaces, tabs)
#Treat: b = Cognitive Behavioral Therapy, f = Familiar Therapy , c = Control Group
#Weight are in pounds

# Rename treatments for clarity
treatment_mapping = {'b': 'Cognitive Behavioral', 'f': 'Family Therapy', 'c': 'Control'}
# Apply mapping to the 'Treat' column
df_an['Treat'] = df_an['Treat'].map(treatment_mapping)

# Convert weights from pounds to kilograms adding them in the dataframe while keeping the original
df_an['Weight1_kg'] = round(df_an['Weight1'] * 0.453592, 1)
df_an['Weight2_kg'] = round(df_an['Weight2'] * 0.453592,1)

### 1. Descriptive Statistics and Repeated Measures ANOVA ###

### Calculate descriptive statistics on weights before and after the experimental period for each treatment. ###

# Calculate descriptive statistics using describe() method
# Descriptive statistics for Weight1_kg (Weight Before Treatment)
desc_W1_kg = df_an.groupby('Treat')['Weight1_kg'].describe().round(2)
desc_W1_kg

# Descriptive statistics for Weight2_kg - After Treatment
desc_W2_kg = df_an.groupby('Treat')['Weight2_kg'].describe().round(2)
desc_W2_kg

### Create box plots to graphically describe the response distributions before and after the experimental period for each treatment. ###

# Create a figure with subplots
treatments = df_an['Treat'].unique()
n_treatments = len(treatments) #number of treatments

fig, axes = plt.subplots(
    nrows=1,  # Number of rows: 1
    ncols=n_treatments,  # Number of columns: one for each treatment
    figsize=(15, 5),  # Size of the figure
    sharey=True  # Share the y-axis between the plots
)

# If only one subplot, ensure axes is iterable
#This allows you to use the same iteration code regardless of whether you have one or multiple subplots
#by converting the single 'axes' object into a list
if n_treatments == 1:
    axes = [axes]

# Plot box plots for each treatment
for i, treatment in enumerate(treatments):
    # Filter data for the current treatment
    treatment_data = df_an[df_an['Treat'] == treatment]

    # Create a box plot for the current treatment
    sns.boxplot(
        data=treatment_data[['Weight1_kg', 'Weight2_kg']],
        ax=axes[i],
        palette='Set2'
    )

    axes[i].set_title(treatment)
    axes[i].set_xlabel('Period')
    axes[i].set_ylabel('Weight (Kg)')

    # Set x-axis tick positions and labels
    axes[i].set_xticks([0, 1])  # Setting positions of the ticks on the x-axis
    axes[i].set_xticklabels(['Before', 'After'])  # assigns labels to the tick positions

# Adjust layout
plt.tight_layout()
plt.show()

### The three treatments have similar distributions originally. There is some evidence of a greater mean weight gain for the family therapy group, though there are a few low outlying weight values. ###

### Compute the sample mean weight, by Treatment and Time of measurement: ###

# Group by 'Treat' and calculate the mean for Weight1 and Weight2
mean_weights = df_an.groupby('Treat').agg({
    'Weight1_kg': 'mean',
    'Weight2_kg': 'mean'
}).reset_index()  # To have the default index instead of hierarchical one (multi-lvl)

# Rename columns
mean_weights.columns = ['Treatment', 'Mean Weight Before', 'Mean Weight After']

# Round the mean values to 2 decimal places
mean_weights = mean_weights.round(2)

# Display the result
print(mean_weights)

### Compute a Repeated Measures ANOVA ###

#The data contain a Within Subject factor: Effect of Time (weight measured before and after the treatment)
#and a Between Subject factor: Effect of Treatment (The type of treatments- 3 independent samples)

#For this type of analysis AnovaRM can't be used since  Calculation of between-subject effects is not yet implemented.
#I tried to use the statistical package Pingouin to calculate mixed ANOVA

# Reshape DataFrame to long format (required by AnovaRM and Pingouin)
# There must be a single Weight column and a Time column - that indicates whether it's the weight before or after the treatment.

df_long = pd.melt(df_an, id_vars=['Subject', 'Treat'],
                  value_vars=['Weight1_kg', 'Weight2_kg'],
                  var_name='Time', value_name='Weight') #time column - Weight1: weight before the treatment , Weight2: after the treatment-

## Check the values in the Time column
#print(df_long['Time'].unique())  # Debugging step - must be ['Weight1' 'Weight2']

# # Failing running the repeated measures ANOVA - AnovaRM
# aovrm = AnovaRM(df_long, 'Weight', 'Subject', within=['Time'], between=['Treat'], aggregate_func='mean')
# res = aovrm.fit()
# #NotImplementedError: Between subject effect not yet supported!

## Recode Time variable as Before or After
df_long['Time'] = df_long['Time'].map({'Weight1_kg': 'Before', 'Weight2_kg': 'After'})
#print(df_long)
## Check for NaN values after mapping
#print(df_long.isnull().sum())  # Debugging step

# Perform the mixed ANOVA using pingouin
aov = pg.mixed_anova(data=df_long, dv='Weight', within='Time', between='Treat', subject='Subject')
print(aov)

### The Interaction (Time*Treatment) row of the ANOVA table indicates that the interaction is highly significant (P-value=0.006).
### The difference between population means for the two times differs according to the treatment, and the difference between population means for a pair of treatments varies according to the time.

### 2. Focused Analysis on Weight Change ###

### Analyze the weight change after the Cognitive Behavioral Therapy. If the change in weight is positive the weight is increased. 

#calculate the weight difference
df_an['Change_kg'] = df_an['Weight2_kg'] - df_an['Weight1_kg']

# Filter the DataFrame to include only rows where 'Treat' is 'Cognitive Behavioral'
df_CB = df_an[df_an['Treat'] == 'Cognitive Behavioral'].copy()

#Display the DataFrame
#print(df_CB)

#Performing some Descriptive statics on the weight change
df_CB = df_CB['Change_kg']
n_observations = len(df_CB)
mean_change = df_CB.mean()
std_change = df_CB.std()
#std_error = std_change / np.sqrt(n_observations) #standard devation/square root of observations
std_error = stats.sem(df_CB)
min_value = df_CB.min()
max_value = df_CB.max()
confidence_level = 0.95
degrees_freedom = n_observations - 1
confidence_interval = stats.t.interval(confidence_level, degrees_freedom, mean_change, std_error)

# Create a DataFrame to store the results
results = pd.DataFrame({
    'Number of Observations': [n_observations],
    'Mean': [mean_change],
    'Standard Deviation': [std_change],
    'Standard Error': [std_error],
    'Min Value':[min_value],
    'Max Value':[max_value],
    'Confidence Interval Lower': [confidence_interval[0]],
    'Confidence Interval Upper': [confidence_interval[1]],
})

# Display the results DataFrame
results

### Visualization of the weight change ###

# Create a figure with subplots
fig, (ax_box, ax_hist) = plt.subplots(
    nrows=2,  # Number of rows: 2 (one for box plot, one for histogram)
    ncols=1,  # Number of columns: 1
    sharex=True,  # Share the x-axis between the plots
    gridspec_kw={"height_ratios": [1, 4]},  # Ratio of box plot to histogram
    figsize=(10, 8)  # Size of the figure
)

# Box plot (top)
sns.boxplot(
    x= df_CB,  # Change in weight on the x-axis
    ax=ax_box,  # Axes to plot on
)
ax_box.set(xlabel='')  # Remove x-axis label for box plot
ax_box.set(title='Box Plot and Histogram of Change in Weight')  # Set title for the combined plots

# Histogram (bottom)
sns.histplot(
    df_CB,  # Change in weight on the x-axis
    ax=ax_hist  # Axes to plot on
)
ax_hist.set(xlabel='Change in Weight (kg)', ylabel='Frequency')  # Set x and y labels for histogram

# Adjust layout
#plt.tight_layout()

# Show the plot
plt.show()

### From descriptive statistic the mean weight change resulted positive. 
### Next step is to perform a one-sided t-test to check if the mean change is significantly greater than 0:

# Perform the One-sided t-test
res_1s = stats.ttest_1samp(df_CB, popmean=0,alternative='greater')
#TtestResult(statistic=2.201031832293535, pvalue=0.018072363635736714, df=28)

# def hypothesis_test_result(p_value, alpha=0.05):
#     """
#     Determines whether to reject or fail to reject the null hypothesis.

#     Parameters:
#     - p_value: The p-value from the t-test.
#     - alpha: The significance level (default is 0.05).

#     Returns:
#     - A string indicating the result of the hypothesis test.
#     """
#     # Adjust the p-value for a one-sided test if needed
#     if p_value <= alpha:
#       result = "Reject the null hypothesis."
#     else:
#       result =  "Fail to reject the null hypothesis."
# # Formulate the output string
#     return f"P-value ({p_value}) <= Alpha ({alpha}): {result}" if p_value <= alpha else f"P-value ({p_value}) > Alpha ({alpha}): {result}"

#Using the obtained p-value, determines whether to reject or fail to reject the null hypothesis.
#whether the Cognitive Behavioral treatment produces increases in weight.
hypothesis_test_result(res_1s.pvalue)
print(hypothesis_test_result(res_1s.pvalue))

### Analyze how the change in weight compares for the treatment group to the control group. 
### If treatment has no effect relative to control, then we would expect the groups to have equal means and equal standard deviations of weight change.

# Filter Anorexic dataframe to include only change in weight for the Control condition
control_df= df_an[df_an['Treat'] == 'Control']['Change_kg']
control_df.mean() #-0.2192
df_CB.mean() #1.3517

# Perform two-sample t-test
res_2samp = stats.ttest_ind(df_CB, control_df, equal_var=False)

##Using the obtained p-value, determines whether to reject or fail to reject the null hypothesis.
print(hypothesis_test_result(res_2samp.pvalue))

###Calculate the effect size for summarizing the size of the difference between the two groups:

# def eff_size(group1, group2):
#     """
#     Calculate Cohen's d for the mean difference between two groups and interpret the effect size.

#     Parameters:
#     group1 (array-like or pd.Series): First group of data.
#     group2 (array-like or pd.Series): Second group of data.

#     Returns:
#     dict: A dictionary with Cohen's d and an interpretation of the effect size.
#     """

#     # Convert inputs to numpy arrays if they are pandas Series or DataFrames
#     if isinstance(group1, (pd.Series, pd.DataFrame)):
#         group1 = group1.values.flatten()  # Flatten in case of DataFrame
#     if isinstance(group2, (pd.Series, pd.DataFrame)):
#         group2 = group2.values.flatten()  # Flatten in case of DataFrame

#     # Calculate means and standard deviations
#     mean1 = np.mean(group1)
#     mean2 = np.mean(group2)
#     std1 = np.std(group1, ddof=1)  # Sample standard deviation (ddof=1)
#     std2 = np.std(group2, ddof=1)

#     # Sample sizes
#     n1 = len(group1)
#     n2 = len(group2)

#     # Pooled Standard Deviation for two independent samples
#     s_pooled = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))

#     # Cohen's d
#     cohens_d = (mean1 - mean2) / s_pooled

#     # Interpretation based on Cohen's d value
#     if abs(cohens_d) < 0.20:
#         interpretation = "Very Small Effect Size"
#     elif abs(cohens_d) < 0.50:
#         interpretation = "Small Effect Size"
#     elif abs(cohens_d) < 0.80:
#         interpretation = "Medium Effect Size"
#     else:
#         interpretation = "Large Effect Size"

#     return {'Cohen\'s d': cohens_d, 'Interpretation': interpretation}

#Calculate the effect size using the function eff_size
ef_s = eff_size(df_CB,control_df)
print(ef_s)
