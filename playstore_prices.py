import pandas as pd

playstore = pd.read_csv("googleplaystore.csv")
print(playstore.shape)

## drop invalid row
playstore = playstore.drop(labels=10472)

## clean characters from Price, convert to float
playstore["Price"] = playstore["Price"].str.replace("$", "").astype("float")

## create dataset that is paid apps only
paid = playstore[playstore["Price"] != 0].copy()

## need to remove characters/convert size column values
def clean_size(size):
    """Convert file size string to float and megabytes"""
    size = size.replace("M","")
    if size.endswith("k"):
        size = float(size[:-1])/1000
    elif size == "Varies with device":
        size = pd.np.NaN
    else:
        size = float(size)
    return size

## remove unnecessary column Type
paid.drop('Type', axis="columns",inplace=True)

## convert column type of Reviews to int
paid["Reviews"] = paid["Reviews"].astype(int)

## use cleaning function on Size column, convert to float
paid["Size"] = paid["Size"].apply(clean_size).astype(float)
paid.info()

## create masks for dupe apps 
app_mask = paid["App"].isin(
    ["Fuzzy Numbers: Pre-K Number Foundation", "Toca Life: City"]
)
category_mask = paid["Category"] == "FAMILY"

## identify row labels
paid[app_mask & category_mask]

## remove duplicate app entries
paid.drop([2151, 4301], inplace=True)
print(paid.duplicated(subset="App").sum())

## sort by Reviews count descending 
paid.sort_values('Reviews', ascending = False,inplace = True)

## remove duplicate app entries; keep first (higher Reviews) entry
paid.drop_duplicates(subset="App",keep="first",inplace=True)

## how many dupe apps do we have? (0)
print(paid.duplicated("App").sum())

## reset index for dataset
paid.reset_index(inplace=True,drop=True)

## create dataset of affordable apps
affordable_apps = paid[paid["Price"]<50].copy()

## create bool masks for cheap and reasonable masks (less than $5 vs $5 or more)
cheap = affordable_apps["Price"]<5
reasonable = affordable_apps['Price']>=5

## histograms to observe spread of app prices
affordable_apps[cheap].hist(column="Price", grid=False,figsize=(12,6))
affordable_apps[reasonable].hist(column="Price", grid=False,figsize=(12,6))

## create affordability column (cheap vs reasonable) in dataset
affordable_apps['affordability'] = affordable_apps.apply( lambda row: "cheap" if row["Price"] < 5 else "reasonable", axis=1)

## scatterplot and correlation for cheap apps (price vs rating) (low corr: -.05)
affordable_apps[cheap].plot(kind="scatter", x="Price", y="Rating")
print(affordable_apps[cheap].corr().loc["Rating", "Price"])

## calculate mean price of cheap apps to use in other analysis
cheap_mean = affordable_apps[cheap]['Price'].mean()

## set price_criterion column in cheap apps - 1 if price < cheap_mean, otherwise 0
affordable_apps.loc[cheap,'price_criterion'] = affordable_apps['Price'].apply(lambda price: 1 if price < cheap_mean else 0)

## scatterplot to observe price vs rating in reasonable apps
affordable_apps[reasonable].plot(kind="scatter",x="Price",y="Rating")

## calculate mean price of reasonable apps for other analysis
reasonable_mean = affordable_apps[reasonable]['Price'].mean()

## set price_criterion for reasonable apps - 1 if price < reasonable_mean
affordable_apps.loc[reasonable,'price_criterion']=affordable_apps['Price'].apply(lambda price: 1 if price < reasonable_mean else 0)

## set genre_count column, which counts genres attributed to app
affordable_apps["genre_count"] = affordable_apps["Genres"].str.count(";")+1

## subtable displaying mean price by affordability and genre_count columns
genres_mean = affordable_apps.groupby(
    ["affordability", "genre_count"]
).mean()[["Price"]]

## function to flag apps that are priced cheaper than their genre's mean price
def label_genres(row):
    """For each segment in `genres_mean`,
    labels the apps that cost less than its segment's mean with `1`
    and the others with `0`."""

    aff = row["affordability"]
    gc = row["genre_count"]
    price = row["Price"]

    if price < genres_mean.loc[(aff, gc)][0]:
        return 1
    else:
        return 0

## apply label_genres function to new column genre_criterion
affordable_apps["genre_criterion"] = affordable_apps.apply(
    label_genres, axis="columns"
)

##subtable displaying mean price by affordability and category columns
categories_mean = affordable_apps.groupby(["affordability", "Category"]).mean()[['Price']]


## function to flag apps that are priced cheaper than their category's mean price
def label_categories (row):
    aff = row["affordability"]
    cat = row['Category']
    price = row['Price']
    if price < categories_mean.loc[(aff,cat)][0]:
        return 1
    else:
        return 0

## apply function to category_criterion column
affordable_apps['category_criterion'] = affordable_apps.apply(label_categories, axis='columns')

## bool mask for app analysis criteria
criteria = ["price_criterion", "genre_criterion", "category_criterion"]

## create column Result that lets us know whether or not criteria is mainly 1 or 0
affordable_apps["Result"] = affordable_apps[criteria].mode(axis='columns')

## create function that returns  max of either price or mean for each app
def NewPrice(row):
    price = row['Price']
    aff = row['affordability']
    if aff == 'cheap':
        return round(max(price,cheap_mean),2)
    else:
        return round(max(price,reasonable_mean),2)

## apply NewPrice function to New Price column in dataset
affordable_apps['New Price'] = affordable_apps.apply(NewPrice,axis ='columns')

## clean Installs column, convert to int
affordable_apps['Installs'] = affordable_apps['Installs'].str.replace("[+,]","").astype(int)

## calculate new Impact column using new/old prices and installs
affordable_apps['Impact'] = (affordable_apps['New Price']-affordable_apps['Price'])*affordable_apps['Installs']

## observe total impact as sum of all; we decide this isn't the best way to determine impact
total_impact = affordable_apps['Impact'].sum()
print(total_impact)
    

