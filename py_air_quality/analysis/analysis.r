# https://www.rdocumentation.org/packages/nlme/versions/3.1-152/topics/gls

library(nlme)

# Read CSV into R
df <- read.csv(file='/home/john/PhD/GitHub/py-air-quality/py_air_quality/data/preprocessed.csv', header=TRUE, sep=';')

head(df)

# model = lm(pm25_internal ~ filter + weekend + pm25_external,
#            data=df)
# summary(model)

model = gls(pm25_internal ~ filter + weekend + pm25_external,
            data=df,
            correlation=corAR1(form=(~timestamp)),
            verbose=TRUE)
